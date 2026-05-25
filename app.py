from flask import Flask, render_template, request
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ── Product list with prices ─────────────────────────────────
products = {
    "Aashirvaad Atta (5kg)": 280,
    "Tata Salt (1kg)": 25,
    "Fortune Sunflower Oil (1L)": 145,
    "Surf Excel (1kg)": 95,
    "Amul Butter (500g)": 265,
    "Britannia Marie Gold (400g)": 55,
    "Horlicks (500g)": 320,
    "Parle-G Biscuits (800g)": 70,
    "Red Label Tea (500g)": 240,
    "Nescafe Classic (100g)": 290,
    "Dettol Soap (75g)": 35,
    "Colgate Toothpaste (200g)": 120,
    "Vim Dish Bar (200g)": 30,
    "Harpic Toilet Cleaner (500ml)": 110,
    "Lifebuoy Handwash (200ml)": 85,
    "Maggi Noodles (70g)": 15,
    "Haldiram's Bhujia (200g)": 95,
    "MDH Garam Masala (100g)": 75,
    "Everest Chili Powder (100g)": 60,
    "Patanjali Honey (500g)": 180,
    "Real Fruit Juice (1L)": 120,
    "Kissan Jam (500g)": 165,
    "Heinz Ketchup (300g)": 110,
    "Lays Classic (52g)": 20,
    "Kurkure Masala (90g)": 20,
    "Oreo Biscuits (120g)": 35,
    "Kit Kat (37g)": 20,
    "5 Star Chocolate (40g)": 20,
    "Amul Milk (1L)": 68,
    "Mother Dairy Curd (400g)": 40,
    "Basmati Rice Dawat (5kg)": 550,
    "Toor Dal (1kg)": 160,
    "Chana Dal (1kg)": 90,
    "Moong Dal (500g)": 75,
    "Besan (500g)": 55,
    "Maida (1kg)": 45,
    "Suji / Rava (500g)": 35,
    "Poha (500g)": 40,
    "Idli Rice (2kg)": 120,
    "Coconut Oil (500ml)": 180,
    "Ghee Amul (200g)": 140,
    "Sugar (1kg)": 45,
    "Jaggery (500g)": 60,
    "Turmeric Powder (100g)": 35,
    "Cumin Seeds (100g)": 70,
    "Mustard Seeds (100g)": 25,
    "Green Cardamom (50g)": 140,
    "Baking Soda (100g)": 25,
    "Tamarind (200g)": 45,
    "Dry Red Chilli (100g)": 55,
}


# ── Database setup ───────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("billing.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            phone         TEXT,
            date          TEXT,
            subtotal      REAL,
            gst           REAL,
            total         REAL
        )
    """)
    conn.commit()
    conn.close()


# ── Today's stats helper ─────────────────────────────────────
def get_today_stats():
    today = datetime.now().strftime("%d-%m-%Y")
    conn  = sqlite3.connect("billing.db")
    cur   = conn.cursor()
    cur.execute(
        "SELECT COUNT(*), SUM(total), SUM(gst) FROM bills WHERE date LIKE ?",
        (today + "%",)
    )
    row     = cur.fetchone()
    conn.close()
    count   = row[0] or 0
    revenue = round(row[1] or 0, 2)
    gst     = round(row[2] or 0, 2)
    return count, revenue, gst


# ── Routes ───────────────────────────────────────────────────
@app.route('/')
def index():
    today_bills, today_revenue, today_gst = get_today_stats()
    return render_template(
        "index.html",
        products      = products,
        today_bills   = today_bills,
        today_revenue = today_revenue,
        today_gst     = today_gst,
    )


@app.route('/generate_bill', methods=['POST'])
def generate_bill():
    customer  = request.form['customer_name']
    phone     = request.form['phone']

    names      = request.form.getlist('product[]')
    quantities = request.form.getlist('quantity[]')
    gsts       = request.form.getlist('gst[]')

    items       = []
    subtotal    = 0
    total_gst   = 0
    gst_summary = {0: 0, 5: 0, 12: 0, 18: 0, 28: 0}

    for i in range(len(names)):

        # Skip rows where no product is selected
        if names[i] == "":
            continue

        # If quantity is left blank, default to 1
        qty_val = quantities[i].strip()
        qty = 1 if qty_val == "" else int(qty_val)
        if qty < 1:
            qty = 1

        gst_percent = int(gsts[i])
        price       = products[names[i]]

        item_price  = price * qty
        gst_amount  = (item_price * gst_percent) / 100
        total       = item_price + gst_amount

        subtotal  += item_price
        total_gst += gst_amount
        gst_summary[gst_percent] += gst_amount

        items.append({
            "product":     names[i],
            "price":       price,
            "qty":         qty,
            "gst_percent": gst_percent,
            "gst_amount":  round(gst_amount, 2),
            "total":       round(total, 2),
        })

    grand_total  = round(subtotal + total_gst, 2)
    current_date = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    # Save to database
    conn = sqlite3.connect("billing.db")
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO bills (customer_name, phone, date, subtotal, gst, total) VALUES (?,?,?,?,?,?)",
        (customer, phone, current_date, round(subtotal, 2), round(total_gst, 2), grand_total)
    )
    bill_id = cur.lastrowid
    conn.commit()
    conn.close()

    return render_template(
        "bill.html",
        customer_name = customer,
        phone         = phone,
        items         = items,
        subtotal      = round(subtotal, 2),
        gst_total     = round(total_gst, 2),
        grand_total   = grand_total,
        gst_summary   = gst_summary,
        bill_id       = bill_id,
        current_date  = current_date,
    )


@app.route('/test')
def test():
    return "Flask is working"


if __name__ == "__main__":
    init_db()
    app.run(debug=True)