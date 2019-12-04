import json
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.views import APIView
from django.core.files.storage import FileSystemStorage

from wand.image import Image as IMG
# from wand.image import Image
from wand.color import Color

from PIL import Image
import PIL.Image
import pytesseract
import difflib
import re
import os

import random

import pathlib
import uuid


class PdftoexcelView(APIView):

    def __init__(self):

        self.invoice_data = ""
        self.po_no = ''
        self.itemsline = False
        self.tax_amount = ''
        self.itemslst = []
        self.invoice_no = ''
        self.customer_no = ''
        self.order_no = ''
        self.invoice_date = ''
        self.gst_no = ''
        self.registered = 'Not Registered'
        self.supply = ''
        self.vendor_name = ''
        self.po_date = ''
        self.invoice_amount = ''
        self.base_amount = ''
        self.cgst_amount = ''
        self.sgst_amount = ''
        self.invoice_hsn_desc = ''
        self.tds = '194C'
        self.tds_rate = '2'
        self.amount_payable = ''
        self.place = ''
        self.tds_amount = ''
        self.invoice_desc = ''
        self.invoice_desc_data2 = ''
        self.invoice_desc_data1 = ''
        self.batch_no = str(random.randint(0, 9999)) + '/' + '2018-19'
        self.hsn_code = ''
        self.cgst = ''
        self.sgst = ''
        self.temp = ""
        self.invoice_date_flag = 0
        self.match_temp = []
        self.billing_flag = 0
        self.desc_eval_flag = 0
        self.desc_line = 0
        self.luf_invoice_amt = 0
        self.luf_flag_gst = 0
        self.airfrnc_fuel = ''
        self.singapore_flag = 0
        self.airindia_base_amt = ''
        self.tax_airindia = ''
        self.airindia_flag = 0
        self.igst_airindia = ''
        self.tax_airindia_nontaxable = ''
        self.igst = ''
        self.goair_flag = 0
        self.go_dev_fee = ''
        self.go_service_fee = ''

    def post(self, request):
        try:
            pdf_count = 0
            images = []

            while pdf_count < (len(request.data)/2):

                pdf_name = "pdf_file"+str(pdf_count)
                pdf = request.data[pdf_name]
                p_type = "pdf_type"+str(pdf_count)
                pdf_type = request.data[p_type]

                if pdf_type in ('indigo', 'air', 'tata'):
                    resol = 150
                    resoln_150 = True
                else:
                    resol = 350
                    resoln_150 = False

                fs = FileSystemStorage()
                filename = fs.save('static/pdf/' + pdf.name.replace(' ', ''), pdf)
                uploaded_file_url = fs.url(filename)

                self.temp_path = str(uuid.uuid4().hex)

                path = "E:\\raviranjann\\pdfreader\\" + uploaded_file_url.replace('/', '\\')

                if not os.path.exists('E:/raviranjann/pdfreader/static/images'):
                    os.makedirs('E:/raviranjann/pdfreader/static/images')

                os.makedirs('E:/raviranjann/pdfreader/static/images/' + self.temp_path)
                os.chmod('E:/raviranjann/pdfreader/static/images/' + self.temp_path, 0777)

                image_path = 'E:/raviranjann/pdfreader/static/images/' + self.temp_path

                image_count = 0

                with IMG(filename=path, resolution=resol) as img:
                    if resoln_150:
                        img.background_color = Color('white')
                        img.alpha_channel = 'remove'
                    with img.convert('png') as converted:
                        converted.save(filename=image_path + '/page.png')
                        image_count += 1

                f = open('E:/raviranjann/pdfreader/static/text/' + self.temp_path + '.txt', 'w')

                image_dir = pathlib.Path(image_path)

                for current_img in image_dir.iterdir():
                    display = pytesseract.image_to_string(PIL.Image.open(current_img).convert("RGB"), lang='eng')
                    f.write(display.encode('utf-8'))

                f.close()
                print("Reading text from the text file..." + self.temp_path)

                self.evaluate_text()
                self.create_invoice_data()
                self.reinitialize_fields()

                pdf_count += 1
                i = 0

                if len(os.listdir('E:/raviranjann/pdfreader/static/images/' + self.temp_path)) == 1:
                    images.append(self.temp_path + '/page.png')
                else:
                    while i < len(os.listdir('E:/raviranjann/pdfreader/static/images/' + self.temp_path)):
                        images.append(self.temp_path + '/page-' + str(i) + '.png')
                        i += 1

            # response = self.temp_path + '.csv'
            # i = 0
            # images = []

            # while i < len(os.listdir('E:/raviranjann/pdfreader/static/images/' + self.temp_path)):
            #     images.append(self.temp_path + '/page-' + str(i) + '.png');
            #     i += 1
            self.file_writting()

            data = {
                "filename": self.temp_path + '.csv',
                "images": images

            }
            return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json', status=200)
        except Exception, e:
            error = e.args[0]
            response = "An error occurred while converting pdf to excel."
            print(error)
            return HttpResponse(json.dumps(response, cls=DjangoJSONEncoder), content_type='application/json',
                                status=500)

    def evaluate_text(self):

        self.fread = open('E:/raviranjann/pdfreader/static/text/' + self.temp_path + '.txt', 'r')

        self.txt = self.fread.readlines()

        for self.line in self.txt:
            self.words = self.line.split()
            # Get the single best match in line

            if len(self.words) > 0:
                print(self.words)

                if 'SpiceJet' in self.words and not self.vendor_name:
                    self.vendor_name = self.words[1] + ' ' + self.words[2]

                if 'GSTIN' in self.words and 'SpiceJet' in self.words and not self.gst_no:
                    self.gst_no = self.words[-1]
                elif 'SpiceJet' in self.vendor_name and 'Invoice' in self.words and not self.invoice_no:
                    self.invoice_no = self.words[-1]
                elif 'SpiceJet' in self.vendor_name and 'Invoice' in self.words and not self.invoice_date:
                    self.invoice_date = self.words[2]
                elif 'SpiceJet' in self.vendor_name and 'Invoice' in self.words and 'Total' in self.words and not self.invoice_amount:
                    self.invoice_amount = self.words[-1]
                    self.tds = ''
                    self.tds_amount = 0
                    self.tds_rate = ''
                    self.cgst = 0
                    self.sgst = 0
                    self.cgst_amount = 0
                    self.sgst_amount = 0
                    self.amount_payable = self.invoice_amount

                if self.goair_flag == 1 and self.go_service_fee == '':
                    self.go_service_fee = self.words[1].replace(',', '')
                    self.goair_total()
                    self.goair_flag = 0

                if self.airindia_base_amt == '' and self.airindia_flag == 1:
                    self.airindia_base_amt = self.words[0].replace(',', '')
                    self.airindia_flag = 0

                if len(self.words) > 2 and self.singapore_flag == 1 and self.vendor_name != 'AIR INDIA LTD.':
                    self.invoice_amount = self.words[4]
                    self.cgst = self.words[6]
                    self.sgst = self.cgst
                    self.supply = 'Service'
                    self.singapore_flag = 0
                    self.luf_tax_cal()

                if self.vendor_name == 'AIR INDIA LTD.' and len(self.words) > 1 and self.words[1] == '9964':
                    self.hsn_code = self.words[1]
                    self.tds = ''
                    self.tds_amount = 0
                    self.tds_rate = ''
                    self.cgst = 0
                    self.sgst = 0
                    self.cgst_amount = 0
                    self.sgst_amount = 0

                if self.luf_invoice_amt == 1:
                    self.invoice_amount = self.words[0]
                    self.invoice_amount = self.invoice_amount.replace(',', '')
                    self.luf_invoice_amt = 0

                if self.luf_flag_gst == 1:
                    self.sgst = self.words[1]
                    self.sgst = self.sgst.replace("(", '')
                    self.sgst = self.sgst.replace(")", '')
                    self.sgst = self.sgst.replace("%", '')
                    self.cgst = self.sgst
                    self.luf_tax_cal()
                    self.luf_flag_gst = 0

                # if self.vendor_name == 'AIR INDIA LTD.' and self.sgst_amount == '' and self.airindia_base_amt != '':
                #     self.tax_airindia = str(float(self.airindia_base_amt) - float(self.invoice_amount))
                #     self.igst_airindia = str(float(self.tax_airindia) - float(self.tax_airindia_nontaxable))
                #     self.cgst_amount = str(float(self.igst_airindia) / 2)
                #     self.sgst_amount = self.cgst_amount

                matches_gsttin_goair = difflib.get_close_matches("Supplier:", self.words, 1, 0.9)
                if matches_gsttin_goair and len(self.words) > 2 and self.words[0] == 'GSTIN' and self.words[
                    2] == 'Supplier:' and not self.gst_no:
                    self.gst_no = self.words[3]

                matches_goair_dev_fee = difflib.get_close_matches("Development", self.words, 1, 0.9)
                if matches_goair_dev_fee and self.words[0] == 'Development':
                    self.go_dev_fee = self.words[1].replace(',', '')

                matches_goair_service_fee = difflib.get_close_matches("Passenger", self.words, 1, 1)
                if matches_goair_service_fee and self.vendor_name == 'Go Airlines Limited' and self.words[
                    0] == 'Passenger' and len(self.words) == 1:
                    self.goair_flag = 1

                matches_goair_vendor_name = difflib.get_close_matches("Subject:", self.words, 1, 0.9)
                if matches_goair_vendor_name and self.words[0] == 'Subject:':
                    self.vendor_name = self.words[1] + " " + self.words[2] + " " + self.words[3]

                matches_british_invoice_date = difflib.get_close_matches("Sent:", self.words, 1, 0.9)
                if matches_british_invoice_date and self.words[0] == 'Sent:':
                    self.invoice_date = self.words[3] + " " + self.words[2] + " " + self.words[4]

                matches_airindia_invdate = difflib.get_close_matches("lnvoloe", self.words, 1, 0.9)
                if matches_airindia_invdate and len(self.words) > 1 and self.words[1] == 'Date':
                    self.invoice_date = self.words[3]

                matches_airindia_totalamt = difflib.get_close_matches("Invoice", self.words, 1, 0.9)
                if matches_airindia_totalamt and len(self.words) > 1 and self.words[
                    1] == 'Invoice' and self.vendor_name == 'AIR INDIA LTD.':
                    self.airindia_flag = 1

                matches_baseamt_airindia = difflib.get_close_matches("Scheduled", self.words, 1, 0.9)
                if matches_baseamt_airindia and self.vendor_name == 'AIR INDIA LTD.' and self.invoice_amount == '':
                    self.tax_airindia_nontaxable = self.words[7].replace(',', '')
                    self.invoice_amount = self.words[8].replace(',', '')
                    self.hsn_code = self.words[3]

                if matches_baseamt_airindia and self.vendor_name == 'Go Airlines Limited':
                    self.base_amount = self.words[7].replace(',', '')
                    self.invoice_amount = self.words[4].replace(',', '')
                    self.igst = self.words[6].replace(',', '')

                matches_airindia_gstno = difflib.get_close_matches("GSTIN", self.words, 1, 0.9)
                if matches_airindia_gstno and self.words[1] == ':' and self.vendor_name == 'AIR INDIA LTD.' and not self.gst_no:
                    self.gst_no = self.words[2]

                matches_airindia_vendor = difflib.get_close_matches("AIR", self.words, 1, 0.9)
                if matches_airindia_vendor and self.words[1] == 'INDIA' and self.words[2] == 'LTD.':
                    self.vendor_name = self.words[0] + " " + self.words[1] + " " + self.words[2]

                matches_singapore_invoice_desc = difflib.get_close_matches("Transportation", self.words, 1, 0.95)
                if matches_singapore_invoice_desc and len(self.words) == 5:
                    self.invoice_desc = self.words[0] + " " + self.words[1] + " " + self.words[2] + " " + self.words[
                        3] + " " + self.words[4]

                matches_singapore_hsn = difflib.get_close_matches("HSN", self.words, 1, 0.95)
                if matches_singapore_hsn and len(self.words) == 3:
                    self.hsn_code = self.words[2]

                matches_singapore_gst_no = difflib.get_close_matches("GSTIN", self.words, 1, 0.95)
                if matches_singapore_gst_no and len(self.words) == 4 and not self.gst_no:
                    self.gst_no = self.words[2]

                matches_singapore_name = difflib.get_close_matches("Singapore", self.words, 1, 0.9)
                if matches_singapore_name and len(self.words) == 9:
                    self.vendor_name = self.words[2] + " " + self.words[3] + " " + self.words[4]
                    self.invoice_date = self.words[8]

                matches_sing_invoice_no = difflib.get_close_matches("Ticket", self.words, 1, 0.9)
                if matches_sing_invoice_no and self.words[0] == 'Ticket' and len(self.words) == 4:
                    self.singapore_flag = 1

                matches_airfrnc_invoice_date = difflib.get_close_matches("Creation", self.words, 1, 0.9)
                if matches_airfrnc_invoice_date and self.words[1] == 'Creation' and len(self.words) == 5:
                    self.invoice_date = self.words[4]

                matches_airfrnc_gst_num = difflib.get_close_matches("Email", self.words, 1, 0.9)
                if matches_airfrnc_gst_num and len(self.words) == 7 and not self.gst_no:
                    self.gst_no = self.words[2]

                matches_airfrnc_invoice_num = difflib.get_close_matches("PASSENGER", self.words, 1, 0.9)
                if matches_airfrnc_invoice_num and self.words[0] == 'PASSENGER' and len(self.words) == 6:
                    self.invoice_no = self.words[5]
                    self.invoice_desc = self.words[0] + " " + self.words[1]

                matches_airfrnc_name = difflib.get_close_matches("France", self.words, 1, 0.9)
                if matches_airfrnc_name and self.words[1] == 'France':
                    self.vendor_name = self.words[0] + " " + self.words[1]
                    self.supply = 'Service'

                matches_airfrnc_invoice = difflib.get_close_matches("DTW", self.words, 1, 0.9)
                if matches_airfrnc_invoice:
                    self.invoice_amount = self.words[3].replace(',', '')
                    self.airfrnc_fuel = self.words[4].replace(',', '')
                    self.luf_tax_cal()

                matches_airfrnc_gst = difflib.get_close_matches('Surcharge', self.words, 1, 0.9)
                if matches_airfrnc_gst:
                    self.cgst = self.words[6].replace('%', '')
                    self.sgst = self.cgst

                matches_hsn_luf = difflib.get_close_matches("Transport", self.words, 1, 0.9)
                if matches_hsn_luf:
                    if self.words[2] == 'passenger' and 'SpiceJet' not in self.vendor_name:
                        self.hsn_code = self.words[6].replace(")", '')
                        self.invoice_desc = self.words[0] + " " + self.words[1] + " " + self.words[2] + " " + \
                                            self.words[3] + " " + self.words[4]

                matches_luf_vendor_name = difflib.get_close_matches("14394133/LUFTHANSA", self.words, 1, 0.9)
                if matches_luf_vendor_name:
                    self.name = self.words[0].split('/')
                    self.name = self.name[1]
                    self.vendor_name = self.name + " " + self.words[1] + " " + self.words[2]

                matches_lufthansa_gst_no = difflib.get_close_matches("GST:", self.words, 1, 0.9)
                if matches_lufthansa_gst_no:
                    if self.words[0] == 'GST:' and not self.gst_no:
                        self.gst_no = self.words[1]

                matches_sgst_pecent = difflib.get_close_matches("CURR", self.words, 1, 0.95)
                if matches_sgst_pecent:
                    self.luf_flag_gst = 1

                matches_lufthansa_invoice_amount = difflib.get_close_matches("Non-taxable", self.words, 1, 0.8)
                if matches_lufthansa_invoice_amount:
                    if len(self.words) == 2:
                        self.luf_invoice_amt = 1
                    else:
                        self.invoice_amount = self.words[2]

                matches_invdate_magma = difflib.get_close_matches("Date", self.words, 1, 0.9)
                if matches_invdate_magma and self.words.__contains__("C1") == 1:
                    self.invoice_date = self.words[3]

                matches_vendor_magma = difflib.get_close_matches("MagmaFincorp", self.words, 1, 0.9)
                if matches_vendor_magma and len(self.words) == 5:
                    self.vendor_name = self.words[0] + " " + self.words[1]

                matches_invoice_magma = difflib.get_close_matches("Total", self.words, 1, 0.9)
                if matches_invoice_magma and len(self.words) == 6:
                    self.invoice_amount = self.words[5].replace(',', '')

                matches_gstamount_magma = difflib.get_close_matches("CGST", self.words, 1, 0.9)
                if matches_gstamount_magma and len(self.words) == 7:
                    self.cgst_amount = self.words[6].replace(',', '')
                    self.sgst_amount = self.cgst_amount

                matches_descinvoice_hcl = difflib.get_close_matches("NVE", self.words, 1, 0.9)
                # print(matches_descinvoice_hcl)
                if self.invoice_desc == '':
                    if matches_descinvoice_hcl and len(self.words) > 7:
                        self.invoice_desc = " ".join(self.words)

                matches_name_hcl = difflib.get_close_matches("Beneficiary", self.words, 1, 0.7)
                if matches_name_hcl and len(self.words) == 6:
                    self.hcl_vendor()

                matches_po_hcl = difflib.get_close_matches("PO", self.words, 1, 0.9)
                if matches_po_hcl and len(self.words) == 10:
                    self.po_no = self.words[3]

                matches_podate_hcl = difflib.get_close_matches("SAP", self.words, 1, 0.9)
                if matches_podate_hcl and len(self.words) > 6:
                    self.po_date = self.words[7]

                matches_invoice_hcl = difflib.get_close_matches("Gross", self.words, 1, 0.9)
                if matches_invoice_hcl:
                    # if self.words[6] == 'Automation)':
                    self.invoice_amount = self.words[2].replace(',', '')

                matches_sgstamount_hcl = difflib.get_close_matches("IN:", self.words, 1, 0.9)
                if matches_sgstamount_hcl:
                    if self.words[1] == 'State' and len(self.words) > 3:
                        self.sgst_amount = self.words[3].replace(',', '')
                        print(self.sgst_amount)

                matches_cgstamount_hcl = difflib.get_close_matches("IN:", self.words, 1, 0.9)
                if matches_cgstamount_hcl:
                    if self.words[1] == 'Central' and len(self.words) > 3:
                        self.cgst_amount = self.words[3].replace(',', '')
                        print(self.cgst_amount)

                matches_gst_hcl = difflib.get_close_matches("29AAACl-Il645P1Z7", self.words, 1, 0.9)
                if matches_gst_hcl:
                    self.gst_no = '29AAACHl645P1Z7'

                matches_invoice = difflib.get_close_matches('1,224,-136.99', self.words, 1, 0.9)
                if matches_invoice and not self.tax_amount:
                    self.sify_invoice()

                matches_invoice_desc_sify = difflib.get_close_matches("EXPRESS", self.words, 1, 0.9)
                if matches_invoice_desc_sify:
                    self.invoice_desc = " ".join(self.words)

                matches_cgst_amount = difflib.get_close_matches("CGST", self.words, 1, 0.9)
                if matches_cgst_amount and len(self.words) > 2 and self.words[1].find('%') == 1:
                    self.sify_cgst()

                matches_sgst_amount = difflib.get_close_matches("SGST", self.words, 1, 0.9)
                if matches_sgst_amount and len(self.words) > 2 and self.words[1].find('%') == 1:
                    self.sify_sgst()

                matches_company_name = difflib.get_close_matches("Beneficiary", self.words, 1, 0.9)
                if matches_company_name and len(self.words) > 6:
                    self.sify_vendor()

                matches_gst = difflib.get_close_matches("GST|N:29AAACS9032R1ZN", self.words, 1, 0.9)
                if matches_gst:
                    self.sifi_tin()

                matches_date = difflib.get_close_matches("lease:", self.words, 1, 1)
                if matches_date:
                    self.sify_invoice_date()

                sifi_matches_po_number = difflib.get_close_matches("PO.No:", self.words, 1, 0.9)
                if sifi_matches_po_number:
                    self.po_no = self.words[2]

                sifi_matches_po_date = difflib.get_close_matches("PO.Date:", self.words, 1, 0.9)
                if sifi_matches_po_date:
                    self.po_date = self.words[2]

                if self.desc_eval_flag and self.desc_line < 2:
                    self.desc_line += 1
                    self.invoice_desc_eval()

                    if self.desc_line == 2:
                        self.desc_eval_flag = 0

                if len(self.words) > 0 and self.words[0] == 'Billlng':
                    self.billing_flag = 1

                if self.billing_flag:
                    if len(self.words) > 1 and self.words[0].isdigit() and int(self.words[0]) > 1000:
                        self.hsn_code = self.words[1]
                        self.billing_flag = 0

                # if len(words) > 0 and words[0] == 'Billlng':

                matches_gst = difflib.get_close_matches('Grand', self.words, 1, 0.9)
                if matches_gst and not self.sgst_amount:
                    self.grand_total()

                if self.gst_no and not self.amount_payable and not self.cgst_amount:
                    if len(self.words) > 0:
                        self.gst_eval()

                if self.match_temp and self.invoice_date_flag == 1:
                    self.invoice_date = self.words[0]
                    self.invoice_date_flag = 0
                elif self.invoice_no and self.invoice_date_flag == 1:
                    self.invoice_date_eval()

                self.match_temp = difflib.get_close_matches("191502/B0/4367", self.words, 1, 1)
                if self.match_temp:
                    self.bill_number_eval()

                matches = difflib.get_close_matches("Invoice", self.words, 1, 0.8)
                if matches:
                    self.invoice_eval()

                matches_gst = difflib.get_close_matches("GST", self.words, 1, 0.6)
                if matches_gst and not self.gst_no:
                    self.gst_no_vendor()

                matches_gst = difflib.get_close_matches("FIEG", self.words, 1, 0.9)
                if matches_gst and not self.gst_no:
                    self.gst_no_client()

                matches_order = difflib.get_close_matches("Order", self.words, 1, 0.6)
                if matches_order:
                    self.order_eval()

                matches_supply = difflib.get_close_matches("Service", self.words, 1, 0.7)
                if matches_supply:
                    self.service_eval()

                matches_place = difflib.get_close_matches("Place", self.words, 1, 0.9)

                if matches_place:
                    self.supplier_location()

                matches_po = difflib.get_close_matches("Purchase", self.words, 1, 0.6)
                if matches_po:
                    self.purchase_eval()

                matches_total_amt = difflib.get_close_matches("Total", self.words, 1, 0.8)
                if matches_total_amt and self.vendor_name != 'AIR INDIA LTD.' and 'SpiceJet' not in self.vendor_name :
                    self.total_amt_eval()

                matches_total_amt = difflib.get_close_matches('INR', self.words, 1, 0.9)
                if matches_total_amt and self.invoice_amount == '':
                    self.total_amount()

                match_word = re.compile(".*RTIV")
                matches_vendor_name = list(filter(match_word.search, self.words))
                if matches_vendor_name:
                    self.rtiv_eval()

                matches_vendor_name = difflib.get_close_matches("For", self.words, 1, 0.8)
                if matches_vendor_name and not self.vendor_name and self.words.__contains__('Price'):
                    self.vendor_name_eval()

                matches_vendor_name = difflib.get_close_matches("For", self.words, 1, 0.8)
                if matches_vendor_name and not self.vendor_name and self.words.__contains__('Private'):
                    self.vendor_name_eval()

                matches_desc = difflib.get_close_matches("Service", self.words, 1, 0.8)
                if matches_desc:
                    i = 0
                    if self.words[i] == "Service" and self.words[i + 1] == "Coverage:":
                        self.services_vendor()

                matches_hsn_desc = difflib.get_close_matches("Description", self.words, 1, 0.8)
                if matches_hsn_desc and not self.invoice_hsn_desc and len(self.words) > 8:
                    self.description_eval()

                matches_invoice_desc = difflib.get_close_matches("Madam,", self.words, 1, 0.8)
                if matches_invoice_desc:
                    self.desc_eval_flag = 1

                match_tds = difflib.get_close_matches("194", self.words, 1, 0.9)
                if match_tds:
                    self.tds_eval()

                    matches = difflib.get_close_matches("** Note :", self.words, 1, 0.6)
                    if matches:
                        self.note_eval()

                    if not self.invoice_amount:
                        self.invoice_amount_cal()

                matches_invoice_desc_air_india = difflib.get_close_matches("Domestic/International", self.words, 1, 0.9)
                if matches_invoice_desc_air_india and not self.invoice_desc and len(self.words) > 6:
                    self.invoice_desc = " ".join(self.words)

                matches_indigo_vendor = difflib.get_close_matches("Aviaiion", self.words, 1, 0.9)
                if matches_indigo_vendor and not self.vendor_name:
                    self.vendor_name = "IndiGo"

                matches_indigo_gst = difflib.get_close_matches("GSTIN", self.words, 1, 0.9)
                if matches_indigo_gst and self.vendor_name == 'IndiGo' and not self.gst_no and len(self.words) > 1 and len(self.words) < 6:
                    self.gst_no = self.words[1].split(':')[1]

                matches_indigo_invoice_no = difflib.get_close_matches("Number", self.words, 1, 0.9)
                if matches_indigo_invoice_no and self.vendor_name == 'IndiGo' and not self.invoice_no and len(self.words) > 1:
                    self.invoice_no = self.words[2] + self.words[3]

                matches_indigo_invoice_date = difflib.get_close_matches("Dale", self.words, 1, 0.9)
                if matches_indigo_invoice_date and not self.invoice_date and len(self.words) > 1:
                    self.invoice_date = self.words[2].decode("utf-8").replace(u"\u2014", "-").encode("utf-8")

                matches_indogo_invoice_amt = difflib.get_close_matches("GrandTl:lla|", self.words, 1, 0.9)
                if matches_indogo_invoice_amt and not self.invoice_amount:
                    self.amount_payable = self.words[-1]
                    self.invoice_amount = self.words[-1]

                matches_tata_vendor = difflib.get_close_matches("TATA", self.words, 1, 0.9)
                if matches_tata_vendor and not self.vendor_name:
                    self.vendor_name = " ".join(self.words)

                matches_tata_gst = difflib.get_close_matches("GSTN", self.words, 1, 0.9)
                if matches_tata_gst and not self.gst_no and len(self.words) < 3:
                    self.gst_no = self.words[1].split(':')[1]

                matches_tata_invoice_no = difflib.get_close_matches("lnvoioe", self.words, 1, 0.9)
                if matches_tata_invoice_no and not self.invoice_no and len(self.words) > 4:
                    self.invoice_no = self.words[-1]
                elif matches_tata_invoice_no and 'Date' in self.words and not self.invoice_date:
                    self.invoice_date = self.words[-1]

                matches_tata_hsn = difflib.get_close_matches("SAC", self.words, 1, 0.9)
                if matches_tata_hsn and not self.hsn_code and 'SpiceJet' not in self.vendor_name:
                    self.hsn_code = self.words[-1]

                if 'Service' in self.words and 'Transport' in self.words and not self.invoice_desc:
                    self.invoice_desc = " ".join(self.words)

        if self.vendor_name == 'IndiGo' or self.vendor_name == 'TATA SIA Airlines Limiled':
            self.tds = ''
            self.tds_amount = 0
            self.tds_rate = ''
            self.cgst = 0
            self.sgst = 0
            self.cgst_amount = 0
            self.sgst_amount = 0
            self.invoice_amount = self.invoice_amount.replace(',', '')
            self.amount_payable = self.invoice_amount

        if not self.base_amount:
            self.base_amount_cal()

        if self.vendor_name.find("MagmaFincorp") == 0:
            self.gst_no = '29AABCM9445K1ZX'
            self.place = 'Bangalore'
            self.invoice_no = self.invoice_no.replace('O', '0')

        elif self.vendor_name.find('PricewaterhouseCoopers') == 0:
            self.gst_no = '29AABCP9181H2ZZ'
            temp_invoice_date = self.invoice_date.split('\xe2\x80\x94')
            if len(temp_invoice_date) > 1:
                self.invoice_date = temp_invoice_date[0] + '-' + temp_invoice_date[1]

        elif self.vendor_name.find('VEiRTIV ENERGY PRIVATE LIMITED') == 0:
            self.vendor_name = 'VERTIV ENERGY PRIVATE LIMITED'
            self.invoice_no = self.invoice_no.replace('I', '/')

        elif self.vendor_name.find('HCL TECHNOLOGIES LIMITED') == 0:
            if not self.invoice_no:
                self.invoice_no = 'D81010106540'

        if self.base_amount and self.cgst_amount and self.sgst_amount:
            self.cgst_sgst_cal()

        if self.vendor_name.find('PricewaterhouseCoopers') == 0 or self.vendor_name.find(
                'Sify') == 0 or self.vendor_name.find('HCL TECHNOLOGIES') == 0 or self.vendor_name.find(
            "MagmaFincorp") == 0:
            self.some_tds_info()

        if self.vendor_name.__contains__('Airlines'):
            self.payable_amount_cal()

        if self.tds and self.tds_rate:
            self.payable_amount_cal()

        if self.invoice_desc_data1 and self.invoice_desc_data2:
            self.invoice_desc = self.invoice_desc_data1 + self.invoice_desc_data2

        if self.gst_no != 0:
            self.registered = 'Registered'

        if self.vendor_name == 'AIR INDIA LTD.':
            # self.air_india_gstpercnt()
            self.airindia_amount_payable()

        print("CGST amount: " + str(self.cgst_amount))
        print("SGST amount: " + str(self.sgst_amount))
        print("vendor name: " + self.vendor_name)
        print("Invoice amount: " + self.invoice_amount)
        print("CGST : " + str(self.cgst))
        print("SGST : " + str(self.sgst))
        print("TDS SECTION: " + self.tds)
        print("TDS RATE: " + self.tds_rate)
        print("AMOUNT PAYABLE: " + str(self.amount_payable))
        print("TDS AMOUNT: " + str(self.tds_amount))
        print("BATCH NO.: " + self.batch_no)
        print("Invoice No:" + self.invoice_no)
        print("HSN NO: " + str(self.hsn_code))
        print("Invoice Date:" + self.invoice_date)
        # print("Vendor GSTIN:" + self.gst_no)
        print("Registered/Unregistered: " + self.registered)
        print("Type of Supply: " + self.supply)
        print("Location of Supplier: " + self.place)
        print("PO Date:" + self.po_date)
        print("PO No:" + self.po_no)
        print("GST CLient: " + self.gst_no)
        print("HSN Description: " + self.invoice_hsn_desc)
        print("Invoice Description: " + self.invoice_desc)
        print("Other Charges: " + self.airfrnc_fuel)


    def goair_total(self):
        self.amount_payable =  str(float(self.base_amount) + float(self.go_service_fee) + float(self.go_dev_fee))
        self.cgst_amount = str(float(self.igst)/2)
        self.sgst_amount = self.cgst_amount
        self.cgst = str((float(self.cgst_amount) * 100)/float(self.invoice_amount))
        self.sgst = self.cgst

    def airindia_amount_payable(self):
        # self.amount_payable = self.airindia_base_amt
        self.amount_payable = str((float(self.invoice_amount)) * ((float(self.sgst) + float(self.cgst)) / 100))
        self.amount_payable = str(float(self.invoice_amount))

    def air_india_gstpercnt(self):
        self.cgst = (float(self.cgst_amount) * 100) / float(self.invoice_amount)
        self.sgst = self.cgst
        self.igst = str(float(self.cgst) + float(self.sgst))

    def luf_tax_cal(self):
        if self.vendor_name != 'Air France':
            self.sgst_amount = (float(self.sgst) / 100) * float(self.invoice_amount)
            self.cgst_amount = (float(self.cgst) / 100) * float(self.invoice_amount)
            self.sgst_amount = str(self.sgst_amount)
            self.cgst_amount = str(self.cgst_amount)
        else:
            self.sgst_amount = float(self.invoice_amount) + float(self.airfrnc_fuel)
            self.sgst_amount = str((float(self.sgst) / 100) * (float(self.sgst_amount)))
            self.cgst_amount = self.sgst_amount

    def invoice_date_eval(self):
        if self.words[0].lower() == 'date' and len(self.words) > 2:
            self.invoice_date = self.words[2]
            self.invoice_date_flag = 0

    def invoice_eval(self):
        i = 0
        while i < len(self.words):
            if self.words[i].lower() == "Invoice".lower():
                if len(self.words) > i + 2:
                    if self.words[i + 1].find('No') == 0:
                        self.invoice_no = self.words[i + 2]
                        self.invoice_date_flag = 1
                        if len(self.invoice_no) < 5 and len(self.words) > i + 3:
                            self.invoice_no = self.words[i + 3]
                        break
            i += 1

    def gst_eval(self):
        if self.words[0].split('-')[0].isdigit() and len(self.words[0]) > 5 and len(self.words) > 1:
            self.base_amount = self.words[0].split('-')[0]
            self.cgst_amount = self.words[1].split('-')[0]
            self.sgst_amount = self.words[1].split('-')[0]

    def grand_total(self):
        if self.words[0] == 'Grand' and self.words[1] == 'Total' and len(self.words) > 2:
            self.cgst_amount = self.words[2].replace(',', '')
            self.sgst_amount = self.cgst_amount

    def bill_number_eval(self):
        self.invoice_date_flag = 1

    def gst_no_client(self):
        i = 0
        while i < len(self.words):
            if self.words[i] == "GST" and self.words[i + 1] == "FIEG":
                if self.words[i + 2] == 'N0.:' and len(self.words) > i + 3:
                    self.gst_no = self.words[i + 3]
                    break
            i += 1

    def gst_no_vendor(self):
        i = 0
        while i < len(self.words):
            if self.words[i].find('GST') == 0 and self.words[1] == ':-' and self.words[1] != 'State':
                if len(self.words) > i + 2 and len(self.words[i + 2]) > 10:
                    self.gst_no = self.words[i + 2]
                    break
            i += 1

    def order_eval(self):
        i = 0
        while i < len(self.words):
            if self.words[i] == "Order":
                if self.words[i + 1] == "Date" and len(self.words) > i + 3:
                    self.order_date = self.words[i + 3]
                    break
            i += 1

    def service_eval(self):
        self.supply = 'Services'

        matches_supply = difflib.get_close_matches("Good", self.words, 1, 0.9)
        if matches_supply:
            self.supply = 'Goods'

    def supplier_location(self):
        if self.vendor_name.find('Sify'):
            self.place = 'Karnataka'
        else:
            i = 0
            while i < len(self.words):
                if self.words[i] == "Place" and len(self.words) > i + 4:
                    if self.words[i + 1] == 'of' and self.words[i + 2].lower() == 'supply':
                        self.place = self.words[i + 4]
                        break
                i += 1

    def purchase_eval(self):
        i = 0
        while i < len(self.words):
            if (self.words[i] == "Purchase") and (self.words[i + 1] == "Order") and not self.po_no:
                if self.words[i + 2] == "No.":
                    self.po_no = self.words[i + 4]
                    pass
                elif self.words[i + 2] == ':':
                    self.po_no = self.words[i + 3]
                    pass
            elif (self.words[i] == "Purchase") and (self.words[i + 1] == "Order") and (self.words[i + 2] == "Date"):
                self.po_date = self.words[i + 4]
                pass
            i += 1

    def total_amt_eval(self):
        i = 0
        while i < len(self.words):
            if (self.words[i] == "Total") and (self.words[i + 1] == "Value"):
                self.invoice_amount = str(int(self.words[i + 2].replace('.', '')) / 100)
                break
            i += 1

    def total_amount(self):
        i = 0
        while i < len(self.words):
            if self.words[i] == 'INR' and len(self.words) > (i + 1) and int(self.words[i + 1]) > 0:
                self.invoice_amount = self.words[i + 1]
                break
            i += 1

    def rtiv_eval(self):
        i = 0
        while i < len(self.words) and self.vendor_name == '':
            if self.words[i].find('rtiv') and (i + 3 < len(self.words)) and self.words[i + 1] == "ENERGY":
                self.vendor_name = self.words[i] + " " + self.words[i + 1] + " " + self.words[i + 2] + " " + self.words[
                    i + 3]
                break
            i += 1

    def vendor_name_eval(self):
        if self.words.__contains__('&'):
            self.vendor_name = self.words[1] + " " + self.words[2] + " " + self.words[3] + " " + self.words[4] + " " + \
                               self.words[5]
        elif self.words[2] == "ENERGY":
            self.vendor_name = self.words[1] + " " + self.words[2] + " " + self.words[3] + " " + self.words[4]
        else:
            self.vendor_name = self.words[1] + " " + self.words[2] + " " + self.words[3]

    def services_vendor(self):
        i = 0
        while i < len(self.words):
            if self.words[i] == "Service" and self.words[i + 1] == "Coverage:":
                self.invoice_desc = self.words[i + 2] + " " + self.words[i + 3] + " " + self.words[i + 4] + " " + \
                                    self.words[i + 5] + " " + self.words[i + 6]
                break
            i += 1

    def description_eval(self):
        if self.words[0] == 'HSN' and self.words[1] == 'Code' and self.words[2] == 'Description':
            self.invoice_hsn_desc = self.words[4] + " " + self.words[5] + " " + self.words[6] + " " + self.words[
                7] + " " + \
                                    self.words[8] + " " + self.words[9]

    def invoice_desc_eval(self):
        i = 0
        while i < len(self.words):
            if self.words[0] == 'We' and self.words[8] == 'INR':
                self.invoice_desc_data1 = " ".join(self.words)
            if self.words[0] == "shall":
                self.invoice_desc_data2 = " ".join(self.words)
            i += 1

    def tds_eval(self):
        i = 0
        while i < len(self.words):
            if self.words[i].find('194') and i + 3 > len(self.words):
                self.tds = self.words[i]
                self.tds_rate = self.words[i + 1]
                self.amout_payable = self.words[i + 2]
                self.tds_amount = self.words[i + 3]
                break
            i += 1

    def note_eval(self):
        self.itemsline = False

        if (self.itemsline) and not (self.matches):
            self.itemslst.append(self.line)

    def base_amount_cal(self):
        if self.cgst_amount and self.invoice_amount != '' and self.vendor_name != 'LUFTHANSA GERMAN AIRLINES':
            self.base_amount = str(float(self.invoice_amount) - float(self.cgst_amount) - float(self.sgst_amount))
        else:
            pass

    def cgst_sgst_cal(self):
        if not self.cgst and self.vendor_name != 'AIR INDIA LTD.':
            self.cgst = (float(self.cgst_amount) * 100) / float(self.base_amount)
            self.sgst = (float(self.sgst_amount) * 100) / float(self.base_amount)

    def invoice_amount_cal(self):
        self.invoice_amount = float(self.cgst_amount) + float(self.base_amount) + float(self.sgst_amount)

    def some_tds_info(self):
        if self.vendor_name.find("MagmaFincorp") == 0:
            self.hsn_code = 998399
        elif self.vendor_name.find("Sify") == 0:
            self.hsn_code = 9984
        elif self.vendor_name.find("HCL") == 0:
            self.hsn_code = 9983
        else:
            self.hsn_code = 9982
        self.tds = '194J'
        self.tds_rate = '10'

    def payable_amount_cal(self):
        if self.base_amount != '' and self.vendor_name != 'Go Airlines Limited' and self.vendor_name != 'LUFTHANSA GERMAN AIRLINES' and self.vendor_name != 'Air France' and self.vendor_name != 'Singapore Airlines Limited' and self.vendor_name != 'AIR INDIA LTD.':
            self.tds_amount = float(self.base_amount) * float(self.tds_rate) / 100
            self.amount_payable = float(self.invoice_amount) - self.tds_amount

        # Calculation for amount_paybale for lufthansa and singapore ...
        elif self.vendor_name == 'LUFTHANSA GERMAN AIRLINES' or self.vendor_name == 'Singapore Airlines Limited':
            self.amount_payable = str(float(self.sgst_amount) + float(self.cgst_amount) + float(self.invoice_amount))
            self.tds_rate = ''
            self.tds = ''

        # Calculation for amount_paybale for Air France...
        elif self.vendor_name == 'Air France':
            self.amount_payable = str(
                float(self.sgst_amount) + float(self.cgst_amount) + float(self.invoice_amount) + float(
                    self.airfrnc_fuel))
            self.tds_rate = ''
            self.tds = ''

        else:
            pass

    def sify_invoice(self):
        self.tax_amount = self.words[2]
        self.invoice_amount = self.words[3]
        self.invoice_amount = self.invoice_amount.replace(',', '')
        self.tax_amount = self.tax_amount.replace(',', '')

    def sify_cgst(self):
        self.cgst = self.words[1]
        self.cgst_amount = self.words[2]
        self.cgst_amount = self.cgst_amount.replace(',', '')

    def sify_sgst(self):
        self.sgst = self.words[1]
        self.sgst_amount = self.words[2]
        self.sgst_amount = self.sgst_amount.replace(',', '')

    def sify_vendor(self):
        self.vendor_name = self.words[2] + " " + self.words[3] + " " + self.words[4]

    def hcl_vendor(self):
        self.vendor_name = self.words[3] + " " + self.words[4] + " " + self.words[5]

    def sifi_tin(self):
        self.gst_no = self.words[0]
        self.gst_no = self.words[0].split(':')
        self.gst_no = self.gst_no[1]

    def sify_invoice_date(self):
        self.invoice_date_flag = 1
        self.invoice_date = self.words[8]
        self.invoice_date = self.invoice_date.split(':')
        self.invoice_date = self.invoice_date[1]

    def reinitialize_fields(self):
        self.po_no = ''
        self.itemsline = False
        self.tax_amount = ''
        self.itemslst = []
        self.invoice_no = ''
        self.customer_no = ''
        self.order_no = ''
        self.invoice_date = ''
        self.gst_no = ''
        self.registered = 'Not Registered'
        self.supply = ''
        self.vendor_name = ''
        self.po_date = ''
        self.invoice_amount = ''
        self.base_amount = ''
        self.cgst_amount = ''
        self.sgst_amount = ''
        self.invoice_hsn_desc = ''
        self.tds = '194C'
        self.tds_rate = '2'
        self.amount_payable = ''
        self.place = ''
        self.tds_amount = ''
        self.invoice_desc = ''
        self.invoice_desc_data2 = ''
        self.invoice_desc_data1 = ''
        self.batch_no = str(random.randint(0, 9999)) + '/' + '2018-19'
        self.hsn_code = ''
        self.cgst = ''
        self.sgst = ''
        self.temp = ""
        self.invoice_date_flag = 0
        self.match_temp = []
        self.billing_flag = 0
        self.desc_eval_flag = 0
        self.desc_line = 0
        self.airfrnc_fuel = ''
        self.singapore_flag = 0
        self.airindia_base_amt = ''
        self.tax_airindia = ''
        self.airindia_flag = 0
        self.igst_airindia = ''
        self.tax_airindia_nontaxable = ''
        self.igst = ''
        self.goair_flag = 0
        self.go_dev_fee = ''
        self.go_service_fee = ''

    def create_invoice_data(self):
        self.invoice_date = self.invoice_date.replace(',','')

        self.invoice_data += self.batch_no + ","
        self.invoice_data += self.invoice_no + ","
        self.invoice_data += self.invoice_date.replace('-', '/') + ","
        self.invoice_data += self.gst_no + ","
        self.invoice_data += self.vendor_name + ","
        self.invoice_data += self.invoice_desc + ","
        self.invoice_data += self.registered + ","
        self.invoice_data += self.supply + ","
        self.invoice_data += self.place.replace(',', '') + ","
        self.invoice_data += str(self.hsn_code) + ","
        self.invoice_data += str(self.invoice_hsn_desc) + ","
        self.invoice_data += str(self.invoice_amount) + ","
        self.invoice_data += self.tds + ","
        self.invoice_data += self.tds_rate + ","
        self.invoice_data += str(self.amount_payable) + ","
        self.invoice_data += str(self.tds_amount) + ","
        self.invoice_data += str(self.base_amount) + ","

        if isinstance(self.cgst, basestring):
            self.invoice_data += self.cgst + ","
        else:
            self.invoice_data += str(round(self.cgst)) + ","

        self.invoice_data += str(self.cgst_amount) + ","

        if isinstance(self.cgst, basestring):
            self.invoice_data += self.sgst + ","
        else:
            self.invoice_data += str(round(self.sgst)) + ","

        self.invoice_data += str(self.sgst_amount) + ","
        self.invoice_data += str(self.airfrnc_fuel) + ","
        self.invoice_data += self.po_date + ","
        self.invoice_data += self.po_no + "\n"

    def file_writting(self):

        f = open('E:/raviranjann/pdfreader/static/csv/' + self.temp_path + '.csv', 'w')

        f.write(
            "Batch No, Invoice No, Invoice Date, Vendor GSTIN, Vendor Name,Invoice Description,Registered/Unregistered,"
            "Type of Supply, Location of Supplier, HSN Code, HSN Description, Invoice Amount,TDS Section, TDS Rate,Amount Payable,TDS Amount,"
            "Base Amt GST, CGST RATE, CGST Amount, SGST RATE, SGST Amount, Other Charges, PO Date, PO No\n"
        )

        f.write(self.invoice_data)

        f.close()



