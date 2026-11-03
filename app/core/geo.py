import math

_BAN_KINH_TRAI_DAT_KM = 6371.0088
_KM_MOI_DO_VI = 111.32


def haversine_km(vi_do_1: float, kinh_do_1: float, vi_do_2: float, kinh_do_2: float) -> float:
    p1, p2 = math.radians(vi_do_1), math.radians(vi_do_2)
    dp = p2 - p1
    dl = math.radians(kinh_do_2 - kinh_do_1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * _BAN_KINH_TRAI_DAT_KM * math.asin(math.sqrt(a))


def bounding_box(vi_do: float, kinh_do: float, ban_kinh_km: float) -> tuple[float, float, float, float]:
    """(viDoMin, viDoMax, kinhDoMin, kinhDoMax) để lọc thô bằng SQL trước khi tính Haversine."""
    d_vi = ban_kinh_km / _KM_MOI_DO_VI
    d_kinh = ban_kinh_km / (_KM_MOI_DO_VI * max(math.cos(math.radians(vi_do)), 0.01))
    return vi_do - d_vi, vi_do + d_vi, kinh_do - d_kinh, kinh_do + d_kinh
