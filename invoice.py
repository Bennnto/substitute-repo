import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import os
import json


class RentalInvoiceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rental Invoice Generator")
        self.root.geometry("800x600")
        self.root.configure(bg="#d3d3d3")

        # Language setting (default: English)
        self.language = "EN"
        
        # Custom line items
        self.custom_items = []
        
        # Language dictionaries
        self.translations = {
            "EN": {
                "title": "Rental Invoice Generator",
                "house_no": "House No.:",
                "tenant_name": "Tenant Name:",
                "rental_fee": "Rental Fee (฿):",
                "hydro": "Hydro (฿):",
                "prev_electric": "Previous Electric Unit:",
                "current_electric": "Current Electric Unit:",
                "calculations": "Calculations",
                "electric_units_used": "Electric Units Used:",
                "electric_cost": "Electric Cost (Units × 7):",
                "total": "Total Amount:",
                "generate": "Save as PDF",
                "clear": "Clear All",
                "add_item": "Add Item",
                "language": "Language: EN",
                "item_description": "Description:",
                "item_amount": "Amount (฿):",
                "invoice_success": "Invoice Generated Successfully!",
                "date": "Date:",
                "invoice_no": "Invoice No:",
                "error_house": "Please enter house number",
                "error_tenant": "Please enter tenant name",
                "error_rental": "Please enter rental fee",
            },
            "TH": {
                "title": "ระบบออกใบแจ้งหนี้ค่าเช่า",
                "house_no": "บ้านเลขที่:",
                "tenant_name": "ชื่อผู้เช่า:",
                "rental_fee": "ค่าเช่า (บาท):",
                "hydro": "ค่าน้ำ (บาท):",
                "prev_electric": "เลขมิเตอร์ไฟก่อนหน้า:",
                "current_electric": "เลขมิเตอร์ไฟปัจจุบัน:",
                "calculations": "การคำนวณ",
                "electric_units_used": "หน่วยไฟฟ้าที่ใช้:",
                "electric_cost": "ค่าไฟฟ้า (หน่วย × 7):",
                "total": "ยอดรวมทั้งหมด:",
                "generate": "บันทึกเป็น PDF",
                "clear": "ล้างข้อมูล",
                "add_item": "เพิ่มรายการ",
                "language": "ภาษา: ไทย",
                "item_description": "รายละเอียด:",
                "item_amount": "จำนวนเงิน (บาท):",
                "invoice_success": "สร้างใบแจ้งหนี้สำเร็จ!",
                "date": "วันที่:",
                "invoice_no": "เลขที่ใบแจ้งหนี้:",
                "error_house": "กรุณากรอกบ้านเลขที่",
                "error_tenant": "กรุณากรอกชื่อผู้เช่า",
                "error_rental": "กรุณากรอกค่าเช่า",
            }
        }

        # Invoice number tracking
        self.invoice_data_file = "invoice_data.json"
        self.load_invoice_number()

        self.create_widgets()

    def create_widgets(self):
        # Language Toggle Button
        self.lang_btn = tk.Button(
            self.root,
            text=self.translations[self.language]["language"],
            command=self.toggle_language,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        self.lang_btn.pack(anchor="ne", padx=20, pady=10)

        # Title
        self.title_label = tk.Label(
            self.root,
            text=self.translations[self.language]["title"],
            font=("Arial", 24, "bold"),
            bg="#d3d3d3",
            fg="#000000",
        )
        self.title_label.pack(pady=10)

        # Main Frame
        main_frame = tk.Frame(self.root, bg="#d3d3d3")
        main_frame.pack(padx=30, pady=10, fill="both", expand=True)

        # House Number
        self.house_label = self.create_field(main_frame, self.translations[self.language]["house_no"], 0)
        self.house_no = tk.Entry(main_frame, width=30, font=("Arial", 12))
        self.house_no.grid(row=0, column=1, pady=10, padx=10, sticky="w")

        # Tenant Name
        self.tenant_label = self.create_field(main_frame, self.translations[self.language]["tenant_name"], 1)
        self.tenant_name = tk.Entry(main_frame, width=30, font=("Arial", 12))
        self.tenant_name.grid(row=1, column=1, pady=10, padx=10, sticky="w")

        # Rental Fee
        self.rental_label = self.create_field(main_frame, self.translations[self.language]["rental_fee"], 2)
        self.rental_fee = tk.Entry(main_frame, width=30, font=("Arial", 12))
        self.rental_fee.grid(row=2, column=1, pady=10, padx=10, sticky="w")
        self.rental_fee.bind("<KeyRelease>", lambda e: self.calculate_total())

        # Hydro
        self.hydro_label = self.create_field(main_frame, self.translations[self.language]["hydro"], 3)
        self.hydro = tk.Entry(main_frame, width=30, font=("Arial", 12))
        self.hydro.grid(row=3, column=1, pady=10, padx=10, sticky="w")
        self.hydro.bind("<KeyRelease>", lambda e: self.calculate_total())

        # Previous Electric Unit
        self.prev_electric_label = self.create_field(main_frame, self.translations[self.language]["prev_electric"], 4)
        self.prev_electric = tk.Entry(main_frame, width=30, font=("Arial", 12))
        self.prev_electric.grid(row=4, column=1, pady=10, padx=10, sticky="w")
        self.prev_electric.bind("<KeyRelease>", lambda e: self.calculate_total())

        # Current Electric Unit
        self.current_electric_label = self.create_field(main_frame, self.translations[self.language]["current_electric"], 5)
        self.current_electric = tk.Entry(main_frame, width=30, font=("Arial", 12))
        self.current_electric.grid(row=5, column=1, pady=10, padx=10, sticky="w")
        self.current_electric.bind("<KeyRelease>", lambda e: self.calculate_total())

        # Separator
        separator = tk.Frame(main_frame, height=2, bg="#cccccc")
        separator.grid(row=6, column=0, columnspan=2, sticky="ew", pady=20)

        # Calculations Display Frame
        self.calc_frame = tk.LabelFrame(
            main_frame,
            text=self.translations[self.language]["calculations"],
            font=("Arial", 12, "bold"),
            bg="#d3d3d3",
            fg="#000000",
            padx=20,
            pady=15,
        )
        self.calc_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=10)

        # Electric Units Used
        self.electric_units_text = tk.Label(
            self.calc_frame,
            text=self.translations[self.language]["electric_units_used"],
            font=("Arial", 11),
            bg="#d3d3d3",
            fg="#000000",
        )
        self.electric_units_text.grid(row=0, column=0, sticky="w", pady=5)
        self.electric_units_label = tk.Label(
            self.calc_frame,
            text="0 units",
            font=("Arial", 11, "bold"),
            bg="#d3d3d3",
            fg="#000000",
        )
        self.electric_units_label.grid(row=0, column=1, sticky="e", pady=5, padx=20)

        # Electric Cost (Units * 7)
        self.electric_cost_text = tk.Label(
            self.calc_frame,
            text=self.translations[self.language]["electric_cost"],
            font=("Arial", 11),
            bg="#d3d3d3",
            fg="#000000",
        )
        self.electric_cost_text.grid(row=1, column=0, sticky="w", pady=5)
        self.electric_cost_label = tk.Label(
            self.calc_frame,
            text="฿0.00",
            font=("Arial", 11, "bold"),
            bg="#d3d3d3",
            fg="#000000",
        )
        self.electric_cost_label.grid(row=1, column=1, sticky="e", pady=5, padx=20)

        # Total
        self.total_text = tk.Label(
            self.calc_frame,
            text=self.translations[self.language]["total"],
            font=("Arial", 14, "bold"),
            bg="#d3d3d3",
            fg="#000000",
        )
        self.total_text.grid(row=2, column=0, sticky="w", pady=10)
        self.total_label = tk.Label(
            self.calc_frame,
            text="฿0.00",
            font=("Arial", 16, "bold"),
            bg="#d3d3d3",
            fg="#000000",
        )
        self.total_label.grid(row=2, column=1, sticky="e", pady=10, padx=20)

        # Configure grid weights for calc_frame
        self.calc_frame.grid_columnconfigure(1, weight=1)

        # Buttons Frame
        button_frame = tk.Frame(self.root, bg="#d3d3d3")
        button_frame.pack(pady=20)

        self.generate_btn = tk.Button(
            button_frame,
            text=self.translations[self.language]["generate"],
            command=self.generate_invoice,
            bg="#2196F3",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=2,
        )
        self.generate_btn.grid(row=0, column=0, padx=10)

        self.clear_btn = tk.Button(
            button_frame,
            text=self.translations[self.language]["clear"],
            command=self.clear_all,
            bg="#FF9800",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=2,
        )
        self.clear_btn.grid(row=0, column=1, padx=10)

        self.add_item_btn = tk.Button(
            button_frame,
            text=self.translations[self.language]["add_item"],
            command=self.add_custom_item,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=2,
        )
        self.add_item_btn.grid(row=0, column=2, padx=10)

    def toggle_language(self):
        """Toggle between English and Thai"""
        self.language = "TH" if self.language == "EN" else "EN"
        self.update_ui_language()

    def update_ui_language(self):
        """Update all UI elements with current language"""
        t = self.translations[self.language]
        
        # Update all labels
        self.lang_btn.config(text=t["language"])
        self.title_label.config(text=t["title"])
        self.house_label.config(text=t["house_no"])
        self.tenant_label.config(text=t["tenant_name"])
        self.rental_label.config(text=t["rental_fee"])
        self.hydro_label.config(text=t["hydro"])
        self.prev_electric_label.config(text=t["prev_electric"])
        self.current_electric_label.config(text=t["current_electric"])
        self.calc_frame.config(text=t["calculations"])
        self.electric_units_text.config(text=t["electric_units_used"])
        self.electric_cost_text.config(text=t["electric_cost"])
        self.total_text.config(text=t["total"])
        self.generate_btn.config(text=t["generate"])
        self.clear_btn.config(text=t["clear"])
        self.add_item_btn.config(text=t["add_item"])

    def create_field(self, parent, label_text, row):
        """Helper to create label fields"""
        label = tk.Label(
            parent,
            text=label_text,
            font=("Arial", 12, "bold"),
            bg="#d3d3d3",
            fg="#000000",
        )
        label.grid(row=row, column=0, sticky="w", pady=10, padx=10)
        return label

    def add_custom_item(self):
        """Add a custom line item to the invoice"""
        t = self.translations[self.language]
        
        # Create a popup window
        popup = tk.Toplevel(self.root)
        popup.title(t["add_item"])
        popup.geometry("400x200")
        popup.configure(bg="#d3d3d3")
        
        # Description field
        desc_label = tk.Label(popup, text=t["item_description"], font=("Arial", 11, "bold"), bg="#d3d3d3", fg="#000000")
        desc_label.pack(pady=10)
        desc_entry = tk.Entry(popup, width=40, font=("Arial", 11))
        desc_entry.pack(pady=5)
        
        # Amount field
        amount_label = tk.Label(popup, text=t["item_amount"], font=("Arial", 11, "bold"), bg="#d3d3d3", fg="#000000")
        amount_label.pack(pady=10)
        amount_entry = tk.Entry(popup, width=40, font=("Arial", 11))
        amount_entry.pack(pady=5)
        
        def save_item():
            desc = desc_entry.get()
            try:
                amount = float(amount_entry.get() or 0)
                if desc:
                    self.custom_items.append({"description": desc, "amount": amount})
                    self.calculate_total()
                    popup.destroy()
            except ValueError:
                pass
        
        # Save button
        save_btn = tk.Button(popup, text="Save", command=save_item, bg="#4CAF50", fg="white", font=("Arial", 11, "bold"))
        save_btn.pack(pady=15)

    def load_invoice_number(self):
        """Load the last invoice number from file"""
        try:
            if os.path.exists(self.invoice_data_file):
                with open(self.invoice_data_file, 'r') as f:
                    data = json.load(f)
                    self.current_invoice_number = data.get('last_invoice_number', 0)
            else:
                self.current_invoice_number = 0
        except:
            self.current_invoice_number = 0

    def save_invoice_number(self):
        """Save the current invoice number to file"""
        try:
            with open(self.invoice_data_file, 'w') as f:
                json.dump({'last_invoice_number': self.current_invoice_number}, f)
        except:
            pass  # Fail silently if can't save

    def get_next_invoice_number(self):
        """Get the next invoice number and increment"""
        self.current_invoice_number += 1
        self.save_invoice_number()
        return f"INV-{self.current_invoice_number:05d}"

    def calculate_total(self):
        """Calculate electric cost and total"""
        try:
            # Get values
            rental = float(self.rental_fee.get() or 0)
            hydro_cost = float(self.hydro.get() or 0)
            prev_electric = float(self.prev_electric.get() or 0)
            current_electric = float(self.current_electric.get() or 0)

            # Calculate units used (current - previous)
            units_used = current_electric - prev_electric
            
            # Ensure units used is not negative
            if units_used < 0:
                units_used = 0

            # Calculate electric cost (units * 7)
            electric_cost = units_used * 7
            
            # Add custom items
            custom_total = sum(item["amount"] for item in self.custom_items)

            # Calculate total
            total = rental + hydro_cost + electric_cost + custom_total

            # Update labels
            self.electric_units_label.config(text=f"{units_used:.0f} units")
            self.electric_cost_label.config(text=f"฿{electric_cost:.2f}")
            self.total_label.config(text=f"฿{total:.2f}")

        except ValueError:
            # If invalid input, show 0
            self.electric_units_label.config(text="0 units")
            self.electric_cost_label.config(text="฿0.00")
            self.total_label.config(text="฿0.00")

    def generate_invoice(self):
        """Generate invoice as PDF"""
        t = self.translations[self.language]
        
        if not self.house_no.get():
            messagebox.showerror("Error", t["error_house"])
            return

        if not self.tenant_name.get():
            messagebox.showerror("Error", t["error_tenant"])
            return

        if not self.rental_fee.get():
            messagebox.showerror("Error", t["error_rental"])
            return

        # Get next invoice number
        invoice_number = self.get_next_invoice_number()
        
        # Ask user where to save the PDF
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=f"{invoice_number}_{self.house_no.get()}.pdf"
        )
        
        if not filename:
            return  # User cancelled
        
        try:
            self.create_pdf(filename, invoice_number)
            messagebox.showinfo(t["invoice_success"], f"PDF saved to:\n{filename}\n\nInvoice No: {invoice_number}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")

    def create_pdf(self, filename, invoice_number):
        """Create PDF invoice"""
        t = self.translations[self.language]
        
        # Get all values
        house = self.house_no.get()
        tenant = self.tenant_name.get()
        rental = float(self.rental_fee.get())
        hydro_cost = float(self.hydro.get() or 0)
        prev_electric = float(self.prev_electric.get() or 0)
        current_electric = float(self.current_electric.get() or 0)
        units_used = current_electric - prev_electric
        if units_used < 0:
            units_used = 0
        electric_cost = units_used * 7
        custom_total = sum(item["amount"] for item in self.custom_items)
        total = rental + hydro_cost + electric_cost + custom_total
        
        invoice_date = datetime.now().strftime("%Y-%m-%d")
        
        # Create PDF
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Register Thai font - try multiple sources
        thai_font_registered = False
        thai_font_name = "ThaiFont"
        
        # Try system fonts first
        thai_font_paths = [
            "/System/Library/Fonts/Supplemental/Thonburi.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Sathu.ttf",
        ]
        
        for font_path in thai_font_paths:
            try:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont(thai_font_name, font_path))
                    thai_font_registered = True
                    break
            except Exception as e:
                continue
        
        # If no system font found, use Helvetica (won't show Thai properly but won't crash)
        if not thai_font_registered:
            thai_font_name = "Helvetica"
        
        
        # Title - Professional header
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height - 40, "RENTAL INVOICE")
        
        # Date and Invoice Number - aligned
        c.setFont("Helvetica", 10)
        y = height - 70
        c.drawString(50, y, f"Date: {invoice_date}")
        c.drawRightString(width - 50, y, f"Invoice No: {invoice_number}")
        
        # Thick separator line
        y -= 15
        c.setLineWidth(2)
        c.line(50, y, width - 50, y)
        c.setLineWidth(1)
        
        # Customer Information Section
        y -= 35
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Customer Information")
        
        c.setFont(thai_font_name, 11)
        y -= 25
        c.drawString(70, y, f"{t['house_no']} {house}")
        y -= 20
        c.drawString(70, y, f"{t['tenant_name']} {tenant}")
        
        # Separator line
        y -= 25
        c.line(50, y, width - 50, y)
        
        # Invoice Details Section
        y -= 35
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Invoice Details")
        
        # Table headers with background
        y -= 30
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(50, y - 5, width - 100, 20, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(70, y, "Description")
        c.drawRightString(width - 70, y, "Amount (THB)")
        
        # Items with better spacing
        c.setFont(thai_font_name, 10)
        y -= 30
        
        # Rental Fee
        c.drawString(70, y, t["rental_fee"].replace(":", "").replace("฿", "").replace("(", "").replace(")", "").strip())
        c.drawRightString(width - 70, y, f"{rental:,.2f}")
        
        y -= 25
        # Hydro
        c.drawString(70, y, t["hydro"].replace(":", "").replace("฿", "").replace("(", "").replace(")", "").strip())
        c.drawRightString(width - 70, y, f"{hydro_cost:,.2f}")
        
        y -= 25
        # Electric
        c.drawString(70, y, f"Electricity ({prev_electric:.0f} → {current_electric:.0f} = {units_used:.0f} units × 7)")
        c.drawRightString(width - 70, y, f"{electric_cost:,.2f}")
        
        # Custom items
        for item in self.custom_items:
            y -= 25
            c.drawString(70, y, item["description"])
            c.drawRightString(width - 70, y, f"{item['amount']:,.2f}")
        
        # Subtotal line
        y -= 20
        c.setLineWidth(0.5)
        c.line(70, y, width - 70, y)
        
        # Total Section - Highlighted
        y -= 35
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(50, y - 10, width - 100, 35, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(70, y, "TOTAL AMOUNT")
        c.setFont("Helvetica-Bold", 18)
        c.drawRightString(width - 70, y, f"THB {total:,.2f}")
        
        # Payment note
        y -= 40
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(70, y, "Currency: Thai Baht (THB)")
        
        # Payment instructions
        y -= 50
        c.setFont("Helvetica-Bold", 10)
        c.drawString(70, y, "Payment Instructions:")
        
        c.setFont("Helvetica", 9)
        y -= 18
        c.drawString(70, y, "Please pay this amount.")
        
        y -= 15
        c.drawString(70, y, "If you have any questions about this invoice, please contact K'Yupapon")
        
        y -= 15
        c.drawString(70, y, "by Phone or WhatsApp.")
        
        # Footer with generation info
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(width/2, 40, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawCentredString(width/2, 28, "Thank you for your business")
        
        # Save PDF
        c.save()

    def clear_all(self):
        """Clear all fields"""
        self.house_no.delete(0, tk.END)
        self.tenant_name.delete(0, tk.END)
        self.rental_fee.delete(0, tk.END)
        self.hydro.delete(0, tk.END)
        self.prev_electric.delete(0, tk.END)
        self.current_electric.delete(0, tk.END)
        self.custom_items = []
        self.electric_units_label.config(text="0 units")
        self.electric_cost_label.config(text="฿0.00")
        self.total_label.config(text="฿0.00")


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = RentalInvoiceGUI(root)
    root.mainloop()
