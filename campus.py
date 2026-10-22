from datetime import timedelta


class BookingPolicy:
    def __init__(self, max_hours, open_time, close_time, priority_rule):
        self.max_hours = float(max_hours)
        self.open_time = open_time
        self.close_time = close_time
        self.priority_rule = priority_rule

    def validate(self, start_datetime, duration):
        if duration <= 0:
            return False, "Duration must be greater than zero."

        if duration > self.max_hours:
            return False, (
                f"Maximum booking duration is "
                f"{self.max_hours:g} hour(s)."
            )

        end_datetime = start_datetime + timedelta(hours=duration)

        opening = start_datetime.replace(
            hour=int(self.open_time[:2]),
            minute=int(self.open_time[3:]),
            second=0,
            microsecond=0
        )

        closing = start_datetime.replace(
            hour=int(self.close_time[:2]),
            minute=int(self.close_time[3:]),
            second=0,
            microsecond=0
        )

        if start_datetime < opening or end_datetime > closing:
            return False, (
                f"Bookings must fall between "
                f"{self.open_time} and {self.close_time}."
            )

        return True, "Booking policy accepted."