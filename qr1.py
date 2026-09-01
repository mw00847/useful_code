import streamlit as st
import pandas as pd

from pathlib import Path
from datetime import datetime
from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_L

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader


# ============================================================
# FILE LOCATIONS
# ============================================================

DATA_DIR = Path(__file__).parent

STOCK_PATH = DATA_DIR / "stock.csv"
TRANSACTIONS_PATH = DATA_DIR / "transactions.csv"


# ============================================================
# INITIALISE CSV FILES
# ============================================================

def initialise_files():

    if not STOCK_PATH.exists():

        stock_df = pd.DataFrame(
            columns=[
                "batch_number",
                "product",
                "starting_stock",
                "current_stock",
                "unit",
            ]
        )

        stock_df.to_csv(
            STOCK_PATH,
            index=False
        )

    if not TRANSACTIONS_PATH.exists():

        transactions_df = pd.DataFrame(
            columns=[
                "timestamp",
                "batch_number",
                "product",
                "quantity",
                "unit",
            ]
        )

        transactions_df.to_csv(
            TRANSACTIONS_PATH,
            index=False
        )


# ============================================================
# LOAD DATA
# ============================================================

def load_stock():

    return pd.read_csv(STOCK_PATH)


def load_transactions():

    return pd.read_csv(TRANSACTIONS_PATH)


# ============================================================
# QR FUNCTIONS
# ============================================================

def make_qr_image(payload):

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(payload)

    qr.make(
        fit=True
    )

    return qr.make_image(
        fill_color="black",
        back_color="white",
    )


def as_pil_rgb(img_like):

    try:
        pil = img_like.get_image()

    except AttributeError:
        pil = img_like

    if pil.mode != "RGB":

        pil = pil.convert(
            "RGB"
        )

    return pil


# ============================================================
# QR PAYLOAD
# ============================================================

def create_stock_qr_payload(
    batch_number,
    quantity,
    unit,
):

    return (
        f"BATCH:{batch_number}|"
        f"QTY:{quantity}|"
        f"UNIT:{unit}"
    )


# ============================================================
# PARSE SCANNED QR
# ============================================================

def parse_stock_qr(
    qr_text
):

    parts = qr_text.strip().split("|")

    data = {}

    for part in parts:

        if ":" not in part:
            continue

        key, value = part.split(
            ":",
            1
        )

        data[
            key.strip().upper()
        ] = value.strip()

    if "BATCH" not in data:

        raise ValueError(
            "QR does not contain a BATCH field."
        )

    if "QTY" not in data:

        raise ValueError(
            "QR does not contain a QTY field."
        )

    if "UNIT" not in data:

        raise ValueError(
            "QR does not contain a UNIT field."
        )

    return data


# ============================================================
# SMALL LABEL PDF
# 50 x 25 mm
# ============================================================

def create_stock_label_pdf(
    batch_number,
    product,
    quantity,
    unit,
):

    payload = create_stock_qr_payload(
        batch_number=batch_number,
        quantity=quantity,
        unit=unit,
    )

    qr_img = make_qr_image(
        payload
    )

    qr_img = as_pil_rgb(
        qr_img
    )

    qr_reader = ImageReader(
        qr_img
    )

    buffer = BytesIO()

    PAGE_W = 50 * mm
    PAGE_H = 25 * mm

    c = canvas.Canvas(
        buffer,
        pagesize=(
            PAGE_W,
            PAGE_H
        )
    )

    # --------------------------------------------------------
    # QR
    # --------------------------------------------------------

    QR_SIZE = 19 * mm

    QR_X = 2 * mm

    QR_Y = (
        PAGE_H
        - QR_SIZE
    ) / 2

    c.drawImage(
        qr_reader,
        QR_X,
        QR_Y,
        QR_SIZE,
        QR_SIZE,
        mask="auto",
    )

    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    TEXT_X = 23 * mm

    y = PAGE_H - 5 * mm

    c.setFont(
        "Helvetica-Bold",
        8
    )

    c.drawString(
        TEXT_X,
        y,
        str(product)
    )

    y -= 5 * mm

    c.setFont(
        "Helvetica",
        6
    )

    c.drawString(
        TEXT_X,
        y,
        "BATCH"
    )

    y -= 3 * mm

    c.setFont(
        "Helvetica-Bold",
        8
    )

    c.drawString(
        TEXT_X,
        y,
        str(batch_number)
    )

    y -= 5 * mm

    c.setFont(
        "Helvetica-Bold",
        10
    )

    c.drawString(
        TEXT_X,
        y,
        f"{quantity} {unit}"
    )

    c.showPage()

    c.save()

    buffer.seek(0)

    return buffer.read()


# ============================================================
# ADD A NEW BATCH
# ============================================================

def add_batch(
    batch_number,
    product,
    quantity,
    unit,
):

    stock_df = load_stock()

    batch_number = (
        str(batch_number)
        .strip()
        .upper()
    )

    existing = stock_df[
        stock_df["batch_number"]
        .astype(str)
        .str.upper()
        == batch_number
    ]

    if not existing.empty:

        raise ValueError(
            f"Batch {batch_number} already exists."
        )

    new_row = pd.DataFrame(
        [
            {
                "batch_number": batch_number,
                "product": product,
                "starting_stock": quantity,
                "current_stock": quantity,
                "unit": unit,
            }
        ]
    )

    stock_df = pd.concat(
        [
            stock_df,
            new_row
        ],
        ignore_index=True,
    )

    stock_df.to_csv(
        STOCK_PATH,
        index=False
    )


# ============================================================
# REMOVE STOCK
# ============================================================

def remove_stock(
    batch_number,
    quantity,
    unit,
):

    stock_df = load_stock()

    batch_number = (
        str(batch_number)
        .strip()
        .upper()
    )

    match = stock_df[
        stock_df["batch_number"]
        .astype(str)
        .str.upper()
        == batch_number
    ]

    if match.empty:

        raise ValueError(
            f"Batch {batch_number} was not found."
        )

    index = match.index[0]

    product = stock_df.loc[
        index,
        "product"
    ]

    stored_unit = str(
        stock_df.loc[
            index,
            "unit"
        ]
    )

    if stored_unit.upper() != unit.upper():

        raise ValueError(
            f"Unit mismatch. "
            f"Batch uses {stored_unit}, "
            f"but QR contains {unit}."
        )

    current_stock = float(
        stock_df.loc[
            index,
            "current_stock"
        ]
    )

    quantity = float(
        quantity
    )

    if quantity <= 0:

        raise ValueError(
            "Quantity must be greater than zero."
        )

    if quantity > current_stock:

        raise ValueError(
            f"Cannot remove {quantity} {unit}. "
            f"Only {current_stock} {unit} remains."
        )

    new_stock = (
        current_stock
        - quantity
    )

    stock_df.loc[
        index,
        "current_stock"
    ] = new_stock

    stock_df.to_csv(
        STOCK_PATH,
        index=False
    )

    # --------------------------------------------------------
    # TRANSACTION LOG
    # --------------------------------------------------------

    transactions_df = load_transactions()

    transaction = pd.DataFrame(
        [
            {
                "timestamp":
                    datetime.now()
                    .strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "batch_number":
                    batch_number,

                "product":
                    product,

                "quantity":
                    quantity,

                "unit":
                    unit,
            }
        ]
    )

    transactions_df = pd.concat(
        [
            transactions_df,
            transaction
        ],
        ignore_index=True,
    )

    transactions_df.to_csv(
        TRANSACTIONS_PATH,
        index=False
    )

    return {
        "batch_number": batch_number,
        "product": product,
        "quantity": quantity,
        "unit": unit,
        "remaining": new_stock,
    }


# ============================================================
# STREAMLIT
# ============================================================

st.set_page_config(
    page_title="QR Stock Control",
    layout="wide",
)

initialise_files()

st.title(
    "QR Stock Control"
)


# ============================================================
# SECTION 1
# CREATE / REGISTER BATCH
# ============================================================

st.header(
    "1. Register New Stock Batch"
)

with st.form(
    "new_batch_form"
):

    col1, col2 = st.columns(
        2
    )

    with col1:

        product = st.text_input(
            "Product"
        )

        batch_number = st.text_input(
            "Batch Number"
        )

    with col2:

        starting_quantity = st.number_input(
            "Starting Quantity",
            min_value=0.0,
            step=1.0,
        )

        unit = st.selectbox(
            "Unit",
            [
                "L",
                "kg",
                "PCS",
            ]
        )

    add_batch_button = (
        st.form_submit_button(
            "Add Batch"
        )
    )


if add_batch_button:

    try:

        add_batch(
            batch_number=batch_number,
            product=product,
            quantity=starting_quantity,
            unit=unit,
        )

        st.success(
            f"Added {product} — "
            f"{batch_number} — "
            f"{starting_quantity} {unit}"
        )

    except Exception as e:

        st.error(
            str(e)
        )


# ============================================================
# SECTION 2
# CREATE SPLIT STOCK LABEL
# ============================================================

st.divider()

st.header(
    "2. Create Stock QR Label"
)

stock_df = load_stock()

if stock_df.empty:

    st.info(
        "Add a stock batch first."
    )

else:

    batch_options = (
        stock_df["batch_number"]
        .astype(str)
        .tolist()
    )

    selected_batch = st.selectbox(
        "Batch",
        batch_options
    )

    selected_row = stock_df[
        stock_df["batch_number"]
        .astype(str)
        == str(selected_batch)
    ].iloc[0]

    selected_product = (
        selected_row["product"]
    )

    selected_unit = (
        selected_row["unit"]
    )

    selected_current_stock = float(
        selected_row[
            "current_stock"
        ]
    )

    st.write(
        f"**Product:** "
        f"{selected_product}"
    )

    st.write(
        f"**Current stock:** "
        f"{selected_current_stock} "
        f"{selected_unit}"
    )

    label_quantity = st.number_input(
        "Quantity for this label",
        min_value=0.01,
        max_value=float(
            selected_current_stock
        )
        if selected_current_stock > 0
        else 0.01,
        step=0.5,
    )

    payload = create_stock_qr_payload(
        batch_number=selected_batch,
        quantity=label_quantity,
        unit=selected_unit,
    )

    st.code(
        payload
    )

    label_pdf = (
        create_stock_label_pdf(
            batch_number=
                selected_batch,

            product=
                selected_product,

            quantity=
                label_quantity,

            unit=
                selected_unit,
        )
    )

    st.download_button(
        "Download QR Label",
        data=label_pdf,
        file_name=(
            f"{selected_batch}_"
            f"{label_quantity}"
            f"{selected_unit}.pdf"
        ),
        mime="application/pdf",
    )


# ============================================================
# SECTION 3
# SCAN STOCK OUT
# ============================================================

st.divider()

st.header(
    "3. Scan Stock"
)

st.caption(
    "Click in the box, then scan a QR label "
    "with the phone."
)

scan_text = st.text_input(
    "Scan QR",
    key="qr_scan",
    placeholder=(
        "BATCH:BATCH001|"
        "QTY:2|UNIT:L"
    ),
)


if scan_text:

    try:

        scan_data = parse_stock_qr(
            scan_text
        )

        result = remove_stock(
            batch_number=
                scan_data["BATCH"],

            quantity=
                scan_data["QTY"],

            unit=
                scan_data["UNIT"],
        )

        st.success(
            f"Removed "
            f"{result['quantity']} "
            f"{result['unit']} "
            f"of {result['product']}"
        )

        st.metric(
            "Remaining Stock",
            (
                f"{result['remaining']} "
                f"{result['unit']}"
            )
        )

        st.write(
            f"Batch: "
            f"**{result['batch_number']}**"
        )

    except Exception as e:

        st.error(
            str(e)
        )


# ============================================================
# SECTION 4
# CURRENT STOCK
# ============================================================

st.divider()

st.header(
    "4. Current Stock"
)

stock_df = load_stock()

st.dataframe(
    stock_df,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# SECTION 5
# TRANSACTION HISTORY
# ============================================================

st.divider()

st.header(
    "5. Stock Movements"
)

transactions_df = (
    load_transactions()
)

if transactions_df.empty:

    st.info(
        "No stock movements yet."
    )

else:

    transactions_df = (
        transactions_df
        .iloc[::-1]
    )

    st.dataframe(
        transactions_df,
        use_container_width=True,
        hide_index=True,
    )
