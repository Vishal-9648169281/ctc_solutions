content = """{% extends "base.html" %}
{% load static %}
{% block title %}Dashboard - CTC Solution{% endblock %}
{% block extra_css %}
<style>
.dt-banner{background:linear-gradient(135deg,#0f1729,#1a237e);border-radius:14px;padding:20px 28px;display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;color:white;}
.dt-date{font-size:1.4rem;font-weight:700;}
.dt-day{font-size:.85rem;opacity:.7;margin-top:2px;}
.dt-time{font-size:2rem;font-weight:800;font-family:monospace;letter-spacing:2px;}
.dt-fy{font-size:.75rem;background:rgba(255,255,255,.1);padding:4px 12px;border-radius:20px;margin-top:8px;display:inline-block;}
.stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px;}
.scard{border-radius:14px;padding:20px;color:white;display:flex;justify-content:space-between;align-items:center;box-shadow:0 4px 15px rgba(0,0,0,.15);}
.scard-num{font-size:2.2rem;font-weight:800;line-height:1;}
.scard-lbl{font-size:.78rem;opacity:.85;margin-top:4px;}
.scard-icon{font-size:2.8rem;opacity:.2;}
.quick-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px;}
.qcard{background:white;border-radius:14px;padding:20px;display:flex;align-items:center;gap:16px;box-shadow:0 2px 12px rgba(0,0,0,.07);text-decoration:none;color:inherit;border:1px solid #e8eaf0;transition:all .2s;}
.qcard:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.12);color:inherit;text-decoration:none;}
.qcard-icon{width:52px;height:52px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;flex-shrink:0;}
.qcard-title{font-size:.9rem;font-weight:700;color:#1a237e;margin-bottom:2px;}
.qcard-sub{font-size:.75rem;color:#64748b;}
.menu-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px;}
.menu-section{background:white;border-radius:14px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.07);border:1px solid #e8eaf0;}
.menu-section-hdr{background:linear-gradient(135deg,#1a237e,#1565c0);color:white;padding:12px 16px;font-size:.82rem;font-weight:700;text-transform:uppercase;display:flex;align-items:center;gap:8px;}
.menu-items{padding:8px 0;}
.menu-item{display:flex;align-items:center;gap:10px;padding:9px 16px;font-size:.83rem;color:#334155;text-decoration:none;transition:all .15s;border-left:3px solid transparent;}
.menu-item:hover{background:#f0f4ff;color:#1a237e;border-left-color:#1a237e;text-decoration:none;}
.menu-item i{font-size:.9rem;width:18px;color:#64748b;}
.menu-item:hover i{color:#1a237e;}
.menu-divider{height:1px;background:#f1f5f9;margin:4px 0;}
.menu-sub{font-size:.68rem;color:#94a3b8;padding:6px 16px 2px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;}
.recent-section{background:white;border-radius:14px;box-shadow:0 2px 12px rgba(0,0,0,.07);overflow:hidden;margin-bottom:24px;}
.recent-hdr{background:linear-gradient(135deg,#1a237e,#1565c0);color:white;padding:13px 20px;font-size:.85rem;font-weight:600;display:flex;justify-content:space-between;align-items:center;}
.recent-hdr a{color:rgba(255,255,255,.8);font-size:.75rem;text-decoration:none;}
.badge-pending{background:#fef3c7;color:#92400e;font-size:.7rem;padding:3px 10px;border-radius:20px;font-weight:600;display:inline-block;}
.badge-paid{background:#d1fae5;color:#065f46;font-size:.7rem;padding:3px 10px;border-radius:20px;font-weight:600;display:inline-block;}
.badge-partial{background:#dbeafe;color:#1e40af;font-size:.7rem;padding:3px 10px;border-radius:20px;font-weight:600;display:inline-block;}
</style>
{% endblock %}
{% block content %}

<div class="dt-banner">
  <div>
    <div class="dt-date" id="d-date">--</div>
    <div class="dt-day" id="d-day">--</div>
    <div class="dt-fy">FY: 01-04-2025 to 31-03-2026</div>
  </div>
  <div style="text-align:center;">
    <div style="font-size:1rem;font-weight:700;">CHANDIGARH TEAM COMPUTERS</div>
    <div style="font-size:.65rem;opacity:.5;margin-top:4px;">Sector 22-B, Chandigarh | Ph: 7986810335</div>
  </div>
  <div style="text-align:right;">
    <div class="dt-time" id="d-time">00:00:00</div>
    <div style="font-size:.7rem;opacity:.6;margin-top:4px;">Current Time</div>
  </div>
</div>

<div class="stats-row">
  <div class="scard" style="background:linear-gradient(135deg,#1a237e,#1565c0);">
    <div><div class="scard-num">{{ total_customers }}</div><div class="scard-lbl">Total Customers</div></div>
    <i class="bi bi-people scard-icon"></i>
  </div>
  <div class="scard" style="background:linear-gradient(135deg,#065f46,#059669);">
    <div><div class="scard-num">{{ total_products }}</div><div class="scard-lbl">Total Products</div></div>
    <i class="bi bi-box scard-icon"></i>
  </div>
  <div class="scard" style="background:linear-gradient(135deg,#7c3aed,#6d28d9);">
    <div><div class="scard-num">{{ total_vendors }}</div><div class="scard-lbl">Total Vendors</div></div>
    <i class="bi bi-shop scard-icon"></i>
  </div>
  <div class="scard" style="background:linear-gradient(135deg,#b45309,#d97706);">
    <div><div class="scard-num">{{ low_stock }}</div><div class="scard-lbl">Low Stock Items</div></div>
    <i class="bi bi-exclamation-triangle scard-icon"></i>
  </div>
</div>

<div class="quick-cards">
  <a href="/sales/invoices/" class="qcard">
    <div class="qcard-icon" style="background:#dbeafe;"><i class="bi bi-receipt-cutoff" style="color:#1a237e;"></i></div>
    <div><div class="qcard-title">GST Invoice</div><div class="qcard-sub">Create and manage invoices</div></div>
  </a>
  <a href="/sales/export/invoice/" class="qcard">
    <div class="qcard-icon" style="background:#d1fae5;"><i class="bi bi-box-arrow-up-right" style="color:#065f46;"></i></div>
    <div><div class="qcard-title">Export Invoice</div><div class="qcard-sub">USD / CAD / INR conversion</div></div>
  </a>
  <a href="/purchase/bills/" class="qcard">
    <div class="qcard-icon" style="background:#ede9fe;"><i class="bi bi-cart-plus" style="color:#7c3aed;"></i></div>
    <div><div class="qcard-title">Purchase Bill</div><div class="qcard-sub">Stock receipt and purchase</div></div>
  </a>
  <a href="/masters/party/" class="qcard">
    <div class="qcard-icon" style="background:#fef3c7;"><i class="bi bi-people" style="color:#92400e;"></i></div>
    <div><div class="qcard-title">Party Master</div><div class="qcard-sub">Customers and vendors</div></div>
  </a>
  <a href="/masters/products/" class="qcard">
    <div class="qcard-icon" style="background:#fce7f3;"><i class="bi bi-box" style="color:#9d174d;"></i></div>
    <div><div class="qcard-title">Item Master</div><div class="qcard-sub">Products and inventory</div></div>
  </a>
  <a href="/payments/receive/" class="qcard">
    <div class="qcard-icon" style="background:#ecfdf5;"><i class="bi bi-cash-coin" style="color:#065f46;"></i></div>
    <div><div class="qcard-title">Payment Receipt</div><div class="qcard-sub">Receive and track payments</div></div>
  </a>
</div>

<div class="menu-grid">
  <div class="menu-section">
    <div class="menu-section-hdr"><i class="bi bi-grid-fill"></i> MASTERS</div>
    <div class="menu-items">
      <a href="/masters/products/" class="menu-item"><i class="bi bi-box"></i> Item Master</a>
      <a href="/masters/rate-modification/" class="menu-item"><i class="bi bi-currency-rupee"></i> Rate Modification</a>
      <div class="menu-divider"></div>
      <a href="/masters/party/" class="menu-item"><i class="bi bi-people"></i> Party Master</a>
      <a href="/masters/company/" class="menu-item"><i class="bi bi-building"></i> Company Master</a>
      <a href="/masters/salesman/" class="menu-item"><i class="bi bi-person-badge"></i> Salesmen Master</a>
      <a href="/masters/area/" class="menu-item"><i class="bi bi-map"></i> Area Master</a>
      <a href="/masters/categories/" class="menu-item"><i class="bi bi-tags"></i> Category Master</a>
      <div class="menu-divider"></div>
      <a href="/masters/gststate/" class="menu-item"><i class="bi bi-geo-alt"></i> GST State Master</a>
      <a href="/masters/gstmaster/" class="menu-item"><i class="bi bi-percent"></i> GST Master</a>
      <a href="/masters/ledger/" class="menu-item"><i class="bi bi-journal-text"></i> General Master</a>
      <a href="/users/" class="menu-item"><i class="bi bi-person-lock"></i> User Master</a>
      <a href="/masters/units/" class="menu-item"><i class="bi bi-rulers"></i> Unit Master</a>
    </div>
  </div>
  <div class="menu-section">
    <div class="menu-section-hdr"><i class="bi bi-arrow-left-right"></i> PURCHASE AND SALES</div>
    <div class="menu-items">
      <div class="menu-sub">Purchase</div>
      <a href="/purchase/bills/" class="menu-item"><i class="bi bi-receipt"></i> Stock Receipt</a>
      <a href="#" class="menu-item"><i class="bi bi-graph-up"></i> Stock Ledger</a>
      <a href="#" class="menu-item"><i class="bi bi-boxes"></i> Current Stock</a>
      <a href="#" class="menu-item"><i class="bi bi-file-minus"></i> Debit Note</a>
      <div class="menu-divider"></div>
      <div class="menu-sub">Sales</div>
      <a href="/sales/invoices/" class="menu-item"><i class="bi bi-receipt-cutoff"></i> GST Invoice</a>
      <a href="/sales/proforma/" class="menu-item"><i class="bi bi-file-earmark-text"></i> GST Proforma Invoice</a>
      <a href="/sales/export/invoice/" class="menu-item"><i class="bi bi-globe"></i> Export Invoice</a>
      <a href="#" class="menu-item"><i class="bi bi-shop-window"></i> Counter Invoice</a>
      <div class="menu-divider"></div>
      <div class="menu-sub">Credit Note</div>
      <a href="/credit-note/" class="menu-item"><i class="bi bi-file-minus"></i> Credit Note Entry</a>
      <a href="#" class="menu-item"><i class="bi bi-file-earmark-bar-graph"></i> Credit Note Statement</a>
    </div>
  </div>
  <div class="menu-section">
    <div class="menu-section-hdr"><i class="bi bi-cash-stack"></i> PAYMENTS AND REPORTS</div>
    <div class="menu-items">
      <div class="menu-sub">Payment Receipt</div>
      <a href="/payments/receive/" class="menu-item"><i class="bi bi-cash-coin"></i> Payment Receipt</a>
      <a href="#" class="menu-item"><i class="bi bi-people"></i> Party Outstanding</a>
      <a href="#" class="menu-item"><i class="bi bi-collection"></i> Collection Report</a>
      <a href="#" class="menu-item"><i class="bi bi-bank"></i> Cheque Printing</a>
      <a href="#" class="menu-item"><i class="bi bi-bank2"></i> Cheque Printing HDFC</a>
      <div class="menu-divider"></div>
      <div class="menu-sub">Reports</div>
      <a href="/reports/" class="menu-item"><i class="bi bi-bar-chart-line"></i> Sale Report LOCAL</a>
      <a href="#" class="menu-item"><i class="bi bi-globe2"></i> Sale Report EXPORT</a>
      <a href="#" class="menu-item"><i class="bi bi-file-earmark-spreadsheet"></i> GSTR Reports</a>
      <a href="#" class="menu-item"><i class="bi bi-table"></i> Itemwise Sale</a>
      <div class="menu-divider"></div>
      <div class="menu-sub">More</div>
      <a href="/accounts/" class="menu-item"><i class="bi bi-journal-bookmarks"></i> Accounts</a>
      <a href="/service/" class="menu-item"><i class="bi bi-telephone-inbound"></i> Call Receive</a>
      <a href="/projects/" class="menu-item"><i class="bi bi-kanban"></i> Project Manager</a>
      <a href="#" class="menu-item"><i class="bi bi-arrow-repeat"></i> Re-Indexing</a>
      <a href="#" class="menu-item"><i class="bi bi-calendar-check"></i> Year Closing</a>
      <a href="/logout/" class="menu-item" style="color:#ef4444;"><i class="bi bi-power"></i> Logout</a>
    </div>
  </div>
</div>

<div class="recent-section">
  <div class="recent-hdr">
    <span><i class="bi bi-clock-history me-2"></i>Recent Invoices</span>
    <a href="/sales/invoices/">View All</a>
  </div>
  <div class="table-responsive">
    <table class="table table-hover mb-0">
      <thead>
        <tr>
          <th>Invoice No</th><th>Customer</th><th>Date</th>
          <th>Type</th><th class="text-end">Amount</th>
          <th>Status</th><th>Action</th>
        </tr>
      </thead>
      <tbody>
        {% for inv in recent_invoices %}
        <tr>
          <td><strong>{{ inv.invoice_number }}</strong></td>
          <td>{{ inv.customer.name }}</td>
          <td>{{ inv.invoice_date|date:"d-m-Y" }}</td>
          <td><span class="badge bg-secondary" style="font-size:.7rem;">{{ inv.get_invoice_type_display }}</span></td>
          <td class="text-end">Rs. {{ inv.total_amount|floatformat:2 }}</td>
          <td><span class="badge-{{ inv.status }}">{{ inv.status|title }}</span></td>
          <td><a href="/sales/invoices/{{ inv.pk }}/" class="btn btn-sm btn-outline-primary py-0 px-2" style="font-size:.75rem;">View</a></td>
        </tr>
        {% empty %}
        <tr><td colspan="7" class="text-center text-muted py-4">No invoices yet. <a href="/sales/invoices/add/">Create first invoice</a></td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

{% endblock %}
{% block extra_js %}
<script>
const DAYS=["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
function pad(n){return String(n).padStart(2,"0");}
function tick(){
  const n=new Date();
  document.getElementById("d-date").textContent=pad(n.getDate())+"-"+pad(n.getMonth()+1)+"-"+n.getFullYear();
  document.getElementById("d-day").textContent=DAYS[n.getDay()];
  document.getElementById("d-time").textContent=pad(n.getHours())+":"+pad(n.getMinutes())+":"+pad(n.getSeconds());
}
tick();setInterval(tick,1000);
</script>
{% endblock %}
"""
with open("templates/dashboard.html","w",encoding="utf-8") as f:
    f.write(content)
print("Dashboard written OK!")
