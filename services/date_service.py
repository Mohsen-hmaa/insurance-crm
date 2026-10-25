import jdatetime
def convert_shamsi_to_date(date_text):
    if not date_text:
        return None
    year, month, day = map(
        int,
        date_text.split("/")
    )
    shamsi_date = jdatetime.date(
        year,
        month,
        day
    )
    return shamsi_date.togregorian()
def convert_date_to_shamsi(date_text):
     if not date_text:
          return ""
     shamsi_date=jdatetime.date.fromgregorian(
          date=date_text
     )
     return shamsi_date.strftime("%Y/%m/%d")