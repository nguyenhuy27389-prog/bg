"""Render HTML and PDF quotes using Jinja2 templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from jinja2 import BaseLoader, Environment, select_autoescape

DEFAULT_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
  <head>
    <meta charset="utf-8" />
    <style>
      body {
        font-family: "DejaVu Sans", "Helvetica", "Arial", sans-serif;
        color: #1a1a1a;
        margin: 0;
        padding: 2.5rem;
        font-size: 14px;
        line-height: 1.5;
      }

      .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        border-bottom: 2px solid #004a99;
        padding-bottom: 1rem;
      }

      .company-info h1 {
        margin: 0;
        font-size: 1.6rem;
        text-transform: uppercase;
        letter-spacing: 0.08rem;
        color: #004a99;
      }

      .company-info p {
        margin: 0.1rem 0;
      }

      .logo img {
        max-height: 80px;
      }

      .quote-title {
        text-align: center;
        margin: 0;
        font-size: 1.8rem;
        letter-spacing: 0.2rem;
        color: #004a99;
      }

      .quote-meta {
        margin: 1.5rem 0;
      }

      .quote-meta p {
        margin: 0.2rem 0;
      }

      table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 1rem;
      }

      th,
      td {
        border: 1px solid #d0d0d0;
        padding: 0.6rem;
        vertical-align: top;
      }

      thead {
        background-color: #f2f6fb;
      }

      th {
        text-transform: uppercase;
        font-size: 0.78rem;
        letter-spacing: 0.08rem;
      }

      .number {
        text-align: right;
        white-space: nowrap;
      }

      .totals {
        margin-top: 1.5rem;
        width: 50%;
        margin-left: auto;
      }

      .totals td {
        border: none;
        padding: 0.3rem 0;
      }

      .totals td.label {
        text-align: left;
      }

      .note {
        margin-top: 2rem;
        border-top: 1px solid #d0d0d0;
        padding-top: 1rem;
      }

      .footer {
        margin-top: 3rem;
        font-size: 0.85rem;
        color: #555;
      }
    </style>
  </head>
  <body>
    <header class="header">
      <div class="company-info">
        <h1>{{ company.name }}</h1>
        {% if company.address %}<p>{{ company.address }}</p>{% endif %}
        {% if company.phone or company.email %}
          <p>
            {% if company.phone %}Điện thoại: {{ company.phone }}{% endif %}
            {% if company.phone and company.email %} | {% endif %}
            {% if company.email %}Email: {{ company.email }}{% endif %}
          </p>
        {% endif %}
        {% if company.website %}<p>Website: {{ company.website }}</p>{% endif %}
        {% if company.tax_code %}<p>MST: {{ company.tax_code }}</p>{% endif %}
      </div>
      {% if company.logo %}
        <div class="logo">
          <img src="{{ company.logo }}" alt="Logo" />
        </div>
      {% endif %}
    </header>

    <h2 class="quote-title">BÁO GIÁ</h2>
    <section class="quote-meta">
      <p><strong>Khách hàng:</strong> {{ customer.name }}</p>
      {% if customer.company %}<p><strong>Đơn vị:</strong> {{ customer.company }}</p>{% endif %}
      {% if customer.address %}<p><strong>Địa chỉ:</strong> {{ customer.address }}</p>{% endif %}
      <p><strong>Ngày báo giá:</strong> {{ quote.date }}</p>
      {% if quote.reference %}<p><strong>Mã báo giá:</strong> {{ quote.reference }}</p>{% endif %}
    </section>

    <table>
      <thead>
        <tr>
          <th style="width: 3rem;">STT</th>
          <th style="width: 7rem;">Mã SP</th>
          <th>Mô tả</th>
          <th style="width: 4rem;">ĐVT</th>
          <th style="width: 5rem;" class="number">Số lượng</th>
          <th style="width: 7rem;" class="number">Đơn giá</th>
          <th style="width: 7rem;" class="number">Thành tiền</th>
        </tr>
      </thead>
      <tbody>
        {% for item in items %}
          <tr>
            <td class="number">{{ loop.index }}</td>
            <td>{{ item.code }}</td>
            <td>
              <strong>{{ item.name }}</strong>
              {% if item.description %}<div>{{ item.description }}</div>{% endif %}
            </td>
            <td>{{ item.unit or "" }}</td>
            <td class="number">{{ item.quantity|quantity }}</td>
            <td class="number">{{ item.unit_price|currency(symbol=quote.currency_symbol) }}</td>
            <td class="number">{{ item.line_total|currency(symbol=quote.currency_symbol) }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>

    <table class="totals">
      <tbody>
        <tr>
          <td class="label">Tạm tính</td>
          <td class="number">{{ summary.subtotal|currency(symbol=quote.currency_symbol) }}</td>
        </tr>
        {% if summary.tax %}
          <tr>
            <td class="label">Thuế ({{ summary.tax.rate }}%)</td>
            <td class="number">{{ summary.tax.amount|currency(symbol=quote.currency_symbol) }}</td>
          </tr>
        {% endif %}
        <tr>
          <td class="label"><strong>Tổng cộng</strong></td>
          <td class="number"><strong>{{ summary.total|currency(symbol=quote.currency_symbol) }}</strong></td>
        </tr>
      </tbody>
    </table>

    {% if quote.note %}
      <section class="note">
        <strong>Ghi chú:</strong>
        <div>{{ quote.note | replace('\n', '<br/>') | safe }}</div>
      </section>
    {% endif %}

    {% if footer %}
      <footer class="footer">{{ footer | replace('\n', '<br/>') | safe }}</footer>
    {% endif %}
  </body>
</html>
"""


def _currency(value: Any, symbol: str = "₫", precision: int | None = None) -> str:
    if value is None:
        return ""
    number = float(value)
    if precision is None:
        precision = 0 if number.is_integer() else 2
    formatted = f"{number:,.{precision}f}"
    return f"{formatted} {symbol}".strip()


def _quantity(value: Any) -> str:
    if value is None:
        return ""
    number = float(value)
    if number.is_integer():
        return f"{int(number)}"
    return f"{number:g}"


def _create_environment() -> Environment:
    env = Environment(
        loader=BaseLoader(),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["currency"] = _currency
    env.filters["quantity"] = _quantity
    return env


def render_html(
    context: Mapping[str, Any], *, template: str = DEFAULT_TEMPLATE
) -> str:
    """Render the quote to HTML using the provided context."""

    env = _create_environment()
    template_obj = env.from_string(template)
    return template_obj.render(**context)


def render_pdf(
    context: Mapping[str, Any],
    output_path: str | Path,
    *,
    template: str = DEFAULT_TEMPLATE,
    base_url: str | None = None,
) -> Path:
    """Render the quote to a PDF file using WeasyPrint."""

    try:
        from weasyprint import HTML
    except ImportError as exc:  # pragma: no cover - informative error path
        raise RuntimeError(
            "WeasyPrint is required to export the quote to PDF. "
            "Install it with `pip install weasyprint`."
        ) from exc

    html_content = render_html(context, template=template)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_content, base_url=base_url).write_pdf(str(output))
    return output


def build_default_context(
    *,
    company: Mapping[str, Any],
    customer: Mapping[str, Any],
    items: Sequence[Mapping[str, Any]],
    summary: Mapping[str, Any],
    quote: Mapping[str, Any],
    footer: str | None = None,
) -> Dict[str, Any]:
    """Assemble a full context dictionary for rendering."""

    context: Dict[str, Any] = {
        "company": company,
        "customer": customer,
        "items": items,
        "summary": summary,
        "quote": quote,
        "footer": footer,
    }
    if "currency_symbol" not in context["quote"]:
        context["quote"] = {
            **context["quote"],
            "currency_symbol": context["quote"].get("currency_symbol", "₫"),
        }
    return context
