ROLE_LEVELS = {
    "کاربر": 1,
    "کاربر ارشد": 2,
    "مدیر": 3,
    "مدیر سیستم": 4,
}
MENU_MIN_ROLES = {
    "marketers": "کاربر ارشد",
    "assignment": "کاربر ارشد",
    "import": "کاربر ارشد",
    "basic_data": "مدیر سیستم",
    "agency_performance": "کاربر ارشد",
    "commission_reports": "کاربر ارشد",
}
def has_minimum_role(role, minimum_role):
    """بررسی می‌کند نقش کاربر به سطح موردنیاز رسیده باشد."""
    user_level = ROLE_LEVELS.get(role, 0)
    required_level = ROLE_LEVELS.get(minimum_role, 0)
    return (
        user_level > 0
        and required_level > 0
        and user_level >= required_level
    )
def can_access_menu(role, menu):
    """بررسی دسترسی به منوهای اصلی برنامه."""
    minimum_role = MENU_MIN_ROLES.get(menu)
    # منوهایی که محدودیت ویژه‌ای ندارند
    if minimum_role is None:
        return True
    return has_minimum_role(role, minimum_role)