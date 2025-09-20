"""Command line interface for generating quotes from product catalogues."""

from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Tuple

from .data_loader import build_product_index, load_products
from .template_renderer import build_default_context, render_pdf

ITEM_SPEC_HELP = "Định dạng mỗi sản phẩm: <ma_sp>:<so_luong>, ví dụ SP01:10"


def _decimal(value: str) -> Decimal:
    try:
        normalised = value.replace(",", ".")
        return Decimal(normalised)
    except (InvalidOperation, AttributeError) as exc:
        raise argparse.ArgumentTypeError(f"Giá trị số không hợp lệ: '{value}'") from exc


def _parse_item_spec(spec: str) -> Tuple[str, Decimal]:
    if ":" not in spec:
        raise argparse.ArgumentTypeError(
            f"Định dạng sản phẩm '{spec}' không hợp lệ. Cần dạng <ma_sp>:<so_luong>."
        )
    code, quantity_str = spec.split(":", 1)
    code = code.strip()
    if not code:
        raise argparse.ArgumentTypeError(
            f"Mã sản phẩm rỗng trong tham số '{spec}'."
        )
    quantity = _decimal(quantity_str)
    if quantity <= 0:
        raise argparse.ArgumentTypeError(
            f"Số lượng phải lớn hơn 0 trong tham số '{spec}'."
        )
    return code, quantity


def _build_items(
    item_specs: Sequence[str],
    product_index: Mapping[str, Mapping[str, object]],
) -> Tuple[List[Dict[str, object]], Decimal]:
    items: List[Dict[str, object]] = []
    subtotal = Decimal("0")
    for spec in item_specs:
        code, quantity = _parse_item_spec(spec)
        product = product_index.get(code)
        if not product:
            raise SystemExit(f"Không tìm thấy sản phẩm với mã '{code}'.")

        unit_price = Decimal(str(product["unit_price"]))
        line_total = (unit_price * quantity).quantize(Decimal("0.01"))
        subtotal += line_total

        items.append(
            {
                "code": product["code"],
                "name": product["name"],
                "description": product.get("description"),
                "unit": product.get("unit"),
                "quantity": float(quantity),
                "unit_price": float(unit_price),
                "line_total": float(line_total),
            }
        )
    return items, subtotal


def _read_template(path: str | None) -> str | None:
    if not path:
        return None
    template_path = Path(path)
    if not template_path.exists():
        raise SystemExit(f"Không tìm thấy file mẫu: {template_path}")
    return template_path.read_text(encoding="utf-8")


def _resolve_logo(logo_path: str | None) -> str | None:
    if not logo_path:
        return None
    path = Path(logo_path)
    if not path.exists():
        raise SystemExit(f"Không tìm thấy file logo: {path}")
    return path.resolve().as_uri()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sinh file báo giá từ danh sách sản phẩm trong Excel.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Đường dẫn tới file Excel chứa danh sách sản phẩm.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Đường dẫn file PDF đầu ra.",
    )
    parser.add_argument(
        "--sheet",
        help="Tên hoặc index của sheet trong Excel (mặc định sheet đầu tiên).",
    )
    parser.add_argument(
        "--template-file",
        help="File HTML tuỳ chỉnh cho mẫu báo giá.",
    )
    parser.add_argument(
        "--customer",
        required=True,
        help="Tên khách hàng hoặc người liên hệ.",
    )
    parser.add_argument(
        "--customer-company",
        help="Tên công ty của khách hàng (nếu có).",
    )
    parser.add_argument(
        "--customer-address",
        help="Địa chỉ khách hàng.",
    )
    parser.add_argument(
        "--items",
        nargs="+",
        required=True,
        help=ITEM_SPEC_HELP,
    )
    parser.add_argument(
        "--company-name",
        default="CÔNG TY TNHH ABC",
        help="Tên công ty phát hành báo giá.",
    )
    parser.add_argument("--company-address", help="Địa chỉ công ty phát hành.")
    parser.add_argument("--company-phone", help="Số điện thoại công ty.")
    parser.add_argument("--company-email", help="Email công ty.")
    parser.add_argument("--company-website", help="Website công ty.")
    parser.add_argument("--company-tax-code", help="Mã số thuế công ty.")
    parser.add_argument("--logo", help="Đường dẫn tới file logo hiển thị trên báo giá.")
    parser.add_argument(
        "--reference",
        help="Mã báo giá hoặc số hợp đồng tham chiếu.",
    )
    parser.add_argument(
        "--date",
        help="Ngày báo giá (mặc định là hôm nay, định dạng DD/MM/YYYY).",
    )
    parser.add_argument(
        "--currency-symbol",
        default="₫",
        help="Ký hiệu tiền tệ sử dụng trong báo giá (ví dụ ₫, đ, VND).",
    )
    parser.add_argument(
        "--tax-rate",
        type=_decimal,
        help="Tỷ lệ thuế VAT (%). Ví dụ 8 hoặc 10.",
    )
    parser.add_argument(
        "--note",
        help="Ghi chú thêm ở cuối báo giá. Có thể xuống dòng bằng \n.",
    )
    parser.add_argument(
        "--footer",
        help="Thông tin chân trang (ví dụ điều khoản thanh toán).",
    )
    parser.add_argument(
        "--base-url",
        help="Đường dẫn cơ sở cho tài nguyên tĩnh (logo, ảnh).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    sheet = args.sheet
    if sheet is not None and sheet.isdigit():
        sheet = int(sheet)

    products = load_products(args.input, sheet_name=sheet)
    product_index = build_product_index(products)

    items, subtotal = _build_items(args.items, product_index)

    tax_info = None
    total = subtotal
    if args.tax_rate is not None:
        tax_rate = args.tax_rate
        tax_amount = (subtotal * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        tax_info = {"rate": float(tax_rate), "amount": float(tax_amount)}
        total = subtotal + tax_amount

    summary = {
        "subtotal": float(subtotal),
        "total": float(total),
    }
    if tax_info:
        summary["tax"] = tax_info

    template_content = _read_template(args.template_file)
    logo_uri = _resolve_logo(args.logo)

    company = {
        "name": args.company_name,
        "address": args.company_address,
        "phone": args.company_phone,
        "email": args.company_email,
        "website": args.company_website,
        "tax_code": args.company_tax_code,
        "logo": logo_uri,
    }

    customer = {
        "name": args.customer,
        "company": args.customer_company,
        "address": args.customer_address,
    }

    quote_date = args.date or datetime.now().strftime("%d/%m/%Y")

    quote = {
        "date": quote_date,
        "reference": args.reference,
        "currency_symbol": args.currency_symbol,
        "note": args.note,
    }

    context = build_default_context(
        company=company,
        customer=customer,
        items=items,
        summary=summary,
        quote=quote,
        footer=args.footer,
    )

    template = template_content if template_content is not None else None
    base_url = args.base_url
    if not base_url and args.template_file:
        base_url = str(Path(args.template_file).resolve().parent)

    if template is None:
        render_pdf(context, args.output, base_url=base_url)
    else:
        render_pdf(context, args.output, template=template, base_url=base_url)


if __name__ == "__main__":  # pragma: no cover
    main()
