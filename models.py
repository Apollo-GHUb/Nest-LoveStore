import polars as pl


def get_recommendations(target_item_id, transactions, items, top_n=6):
    target_info = items.filter(pl.col("item_id") == target_item_id)
    if target_info.height == 0:
        return []

    target_row = target_info.row(0, named=True)
    t_cat_l1 = target_row.get("category_l1") or ""
    t_cat_l2 = target_row.get("category_l2") or ""
    t_cat_l3 = target_row.get("category_l3") or ""
    t_size = str(target_row.get("size") or "").strip().upper()

    # ---------------------------------------------------------
    # TIÊU CHÍ 1: Similar category (Cùng L3 hoặc L2)
    # ---------------------------------------------------------
    similar_pool = items.filter(pl.col("item_id") != target_item_id)
    if t_cat_l3:
        similar_pool = similar_pool.filter(
            (pl.col("category_l3") == t_cat_l3) | (pl.col("category_l2") == t_cat_l2))
    elif t_cat_l2:
        similar_pool = similar_pool.filter(pl.col("category_l2") == t_cat_l2)

    if similar_pool.height == 0:
        return []

    # ---------------------------------------------------------
    # TIÊU CHÍ 2: Co-buy (Số lần mua chung)
    # ---------------------------------------------------------
    if transactions.height > 0:
        customers_who_bought = transactions.filter(
            pl.col("item_id") == target_item_id).select("customer_id").unique()
        if customers_who_bought.height > 0:
            co_purchases = (
                transactions.join(customers_who_bought,
                                  on="customer_id", how="inner")
                .filter(pl.col("item_id") != target_item_id)
                .group_by("item_id").agg(pl.len().alias("so_lan_mua_cung"))
            )
            similar_pool = similar_pool.join(co_purchases, on="item_id", how="left").with_columns(
                pl.col("so_lan_mua_cung").fill_null(0))
        else:
            similar_pool = similar_pool.with_columns(
                pl.lit(0).alias("so_lan_mua_cung"))
    else:
        similar_pool = similar_pool.with_columns(
            pl.lit(0).alias("so_lan_mua_cung"))

    # ---------------------------------------------------------
    # TIÊU CHÍ 3: Điểm ưu tiên Size (Chỉ áp dụng cho Tã)
    # ---------------------------------------------------------
    similar_pool = similar_pool.with_columns(pl.lit(1.0).alias("score_upsale"))

    if "TÃ" in t_cat_l1.upper() and t_size:
        size_order = ["NB", "S", "M", "L", "XL", "XXL", "XXXL"]
        if t_size in size_order:
            t_idx = size_order.index(t_size)

            def get_upsale_score(i_size):
                if not i_size:
                    return 1.0
                i_size = str(i_size).strip().upper()
                if i_size not in size_order:
                    return 1.0
                i_idx = size_order.index(i_size)

                # --- THAY ĐỔI THEO ĐÚNG YÊU CẦU CỦA BẠN ---
                if i_idx == t_idx:
                    return 2.0           # Cùng size: ĐIỂM CAO NHẤT
                elif i_idx == t_idx + 1:
                    return 1.5     # To hơn 1 size: Điểm ít hơn
                elif i_idx == t_idx + 2:
                    return 1.2     # To hơn 2 size: Điểm ít hơn nữa
                elif i_idx > t_idx + 2:
                    return 1.0      # Quá to
                else:
                    return 0.0                        # Nhỏ hơn: Đánh 0 điểm để loại bỏ

            similar_pool = similar_pool.with_columns(pl.col("size").map_elements(
                get_upsale_score, return_dtype=pl.Float64).alias("score_upsale"))

            # LOẠI BỎ KHÔNG ĐỀ XUẤT: Xóa các sản phẩm bị 0 điểm (Size nhỏ hơn)
            similar_pool = similar_pool.filter(pl.col("score_upsale") > 0.0)

    # CÔNG THỨC CHUNG: Final Score = so_lan_mua_cung x score_upsale
    similar_pool = similar_pool.with_columns(
        ((pl.col("so_lan_mua_cung") + 0.1) * pl.col("score_upsale")).alias("final_score"))

    # Trả về 1 danh sách duy nhất
    return similar_pool.sort(["final_score", "score_upsale", "so_lan_mua_cung"], descending=[True, True, True]).head(top_n).to_dicts()
