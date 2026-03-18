import os
from flask import Flask, render_template, request, url_for
import polars as pl
from models import get_recommendations

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))

try:
    items_path = os.path.join(BASE_DIR, 'data', 'items.parquet')
    trans_path = os.path.join(BASE_DIR, 'data', 'transactions-2025-12.parquet')

    items_df = pl.read_parquet(items_path)

    for col in ["category_l1", "category_l2", "category_l3"]:
        if col in items_df.columns:
            items_df = items_df.with_columns(
                pl.col(col).fill_null("").str.strip_chars())

    # SỬ DỤNG REGEX ĐỂ BÓC TÁCH SIZE VÀ PIECE CHO TÃ
    if "description" in items_df.columns:
        items_df = items_df.with_columns(pl.col("description").fill_null(""))

        # Bóc tách Size
        items_df = items_df.with_columns(
            pl.when(pl.col("category_l1").str.to_lowercase().str.contains("tã"))
            .then(pl.col("description").str.extract(r"(?i)\bsize\s*[:\-]?\s*(NB|S|M|L|XL|XXL|XXXL)\b", 1).str.to_uppercase())
            .otherwise(pl.col("size") if "size" in items_df.columns else pl.lit(None))
            .alias("size")
        )

        # Bóc tách Piece
        items_df = items_df.with_columns(
            pl.when(pl.col("category_l1").str.to_lowercase().str.contains("tã"))
            .then(pl.col("description").str.extract(r"(?i)(\d+)\s*miếng", 1))
            .otherwise(pl.col("piece") if "piece" in items_df.columns else pl.lit(None))
            .alias("piece")
        )

    # Bổ sung Regex quét trên tên SP nếu Description bị thiếu
    items_df = items_df.with_columns(
        pl.when((pl.col("category_l1").str.to_lowercase(
        ).str.contains("tã")) & (pl.col("size").is_null()))
        .then(pl.col("category_l3").str.extract(r"(?i)\b(NB|S|M|L|XL|XXL|XXXL)\b", 1).str.to_uppercase())
        .otherwise(pl.col("size"))
        .alias("size")
    )

    items_df = items_df.with_columns(
        pl.when((pl.col("category_l1").str.to_lowercase().str.contains(
            "tã")) & (pl.col("piece").is_null()))
        .then(pl.col("category_l3").str.extract(r"(?i)(\d+)\s*miếng", 1))
        .otherwise(pl.col("piece"))
        .alias("piece")
    )

    transactions_df = pl.read_parquet(trans_path).drop_nulls(
        subset=["customer_id", "item_id"])
    items_clean = items_df.filter(pl.col("category_l3") != "")

    nav_categories = items_clean.group_by("category_l1").agg(pl.len().alias("count")).filter(
        pl.col("count") > 0).sort("count", descending=True).head(6).get_column("category_l1").to_list()
except Exception as e:
    print(f"❌ LỖI TẢI DỮ LIỆU: {e}")
    items_df = pl.DataFrame()
    transactions_df = pl.DataFrame()
    items_clean = pl.DataFrame()
    nav_categories = []


@app.route('/')
def home():
    cat_filter = request.args.get('category')
    search_query = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    ITEMS_PER_PAGE = 20

    filtered = items_clean
    if cat_filter and cat_filter != "all":
        filtered = filtered.filter((pl.col("category_l1") == cat_filter) | (
            pl.col("category_l2") == cat_filter))

    if search_query:
        search_lower = search_query.lower()
        filtered = filtered.filter(
            pl.col("category_l1").str.to_lowercase().str.contains(search_lower) |
            pl.col("category_l2").str.to_lowercase().str.contains(search_lower) |
            pl.col("category_l3").str.to_lowercase().str.contains(search_lower)
        )

    total_items = filtered.height
    total_pages = (total_items + ITEMS_PER_PAGE -
                   1) // ITEMS_PER_PAGE if total_items > 0 else 1
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * ITEMS_PER_PAGE
    sample_products = filtered.slice(
        offset, ITEMS_PER_PAGE).to_dicts() if total_items > 0 else []

    return render_template('index.html', products=sample_products, categories=nav_categories, current_cat=cat_filter, search_query=search_query, page=page, total_pages=total_pages, total_items=total_items)


@app.route('/product/<item_id>')
def product_detail(item_id):
    target_info = items_df.filter(pl.col("item_id") == item_id)
    if target_info.height == 0:
        return "Không tìm thấy sản phẩm", 404
    product = target_info.row(0, named=True)

    recs = get_recommendations(item_id, transactions_df, items_df, top_n=6)

    return render_template('detail.html', product=product, recs=recs, categories=nav_categories)


@app.route('/cart')
def cart(): return render_template('cart.html', categories=nav_categories)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
