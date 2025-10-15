# import qrcode
# import pyqrcode
# import frappe
# from frappe import _
# from frappe.utils import pdf




# def get_context(self):
#     text = "Gaurav"
#     img = qrcode.make(text)
#     img_buffer = pdf.get_image_buffer_from_file(img, format='PNG')
#     img_url = pdf.save_image(img_buffer.getvalue(), "QR Code.png", self.doctype, self.name)
#     return {
#         "qr_code_url": img_url,
#     }
# import frappe
# import qrcode
# import random
# from io import BytesIO
# from PIL import Image
# from frappe.utils import file_manager
# from frappe.utils.file_manager import get_file_path, get_files_path
# from frappe.client import attach_file


# def get_context(context):
#     # /Users/shahilkhan/Downloads/17070.pdf
#     with open('/Users/shahilkhan/Downloads/17070.pdf', 'rb') as f:
#         pdf_data = f.read()
#     # print(pdf_data,'pdf_data')
#     # Generate the QR code image from the PDF data
#     # qr = qrcode.QRCode(version=1, box_size=10, border=4)
#     qrcode_img = qrcode.make(qr)
#     print(qrcode_img)
#     # qr.add_data(pdf_data)
    
#     # # qr.make(fit=True)
#     # print(qr,'pdfpdf')
#     # qr_img = qr.make_image(fill_color="black", back_color="white")
#     # print(qr_img,'qr_img')
#     # # Create a new PDF document
#     # pdf = canvas.Canvas("qr_code.pdf")

#     # # Draw the QR code on the PDF document
#     # pdf.drawInlineImage(qr_img, 100, 500)

#     # # Save the PDF document
#     # pdf.save()
#     return context


    # bench --site dev.localhost install-app pibicut

# qr code with link
# def get_context(context):
#     doc = frappe.get_doc('SAP Item Master', '123456')
# #     # Generate the QR code image
#     resto_url = "https://stechies.com/"
#     qrcode_img = qrcode.make(resto_url)

# #     # Create a new PIL Image object
#     canvas = Image.new("RGB", (380,380), "white")
#     canvas.paste(qrcode_img)

# #     # Create a BytesIO buffer to store the image data
#     buffer = BytesIO()

#     # Save the image to the buffer in PNG format
#     canvas.save(buffer, "PNG")
#     print(canvas,'canvas')

#     # Save the image as a file attachment to the document
#     file_name = f"QR Code {random.randint(0,9999)}.png"
#     print(file_name,'file_name')
#     print(type(file_name),'type of file_name')
#     # print(buffer.getvalue(),'buffer.getvalue()')
#     file_obj = file_manager.save_file(file_name, doc.item_code, 'SAP Item Master', doc.item_code)
#     # print(file_obj,'file_obj')

#     file_path = get_file_path(file_obj.file_url)
#     print(file_path)
#     doc.qr_code = file_path
#     doc.save()
#     frappe.db.commit()

#     context={
       
#         "image":doc.qr_code
#     }
#     # print(context['qrgen'])
#     return context