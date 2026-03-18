#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Неизвестная команда!"
NONPOSITIVE_VALUE_MSG = "Значение должно быть больше нуля!"
INCORRECT_DATE_MSG = "Неправильная дата!"
OP_SUCCESS_MSG = "Добавлено"


def is_leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    parts_of_date = maybe_dt.split("-")
    if len(parts_of_date) != 3:
        return None

    day, month, year = parts_of_date

    if not (day.isdigit() and month.isdigit() and year.isdigit()):
        return None

    day = int(day)
    month = int(month)
    year = int(year)

    if not (1 <= month <= 12):
        return None

    days_in_month = [
        31,
        29 if is_leap_year(year) else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]

    if not (1 <= day <= days_in_month[month - 1]):
        return None

    return day, month, year


def parse_amount(raw: str) -> float | None:
    raw = raw.replace(",", ".")
    if raw.count(".") > 1:
        return None

    for ch in raw:
        if not (ch.isdigit() or ch == "."):
            return None
    
    return float(raw)


def validate_category(cat: str) -> bool:
    for ch in cat:
        if ch in ",. ":
            return False
    return True


def income_handler(incomes: list, raw_amount: str, raw_date: str) -> str:
    amount = parse_amount(raw_amount)
    if amount is None or amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    date = extract_date(raw_date)
    if date is None:
        return INCORRECT_DATE_MSG

    incomes.append((amount, date))

    return OP_SUCCESS_MSG


def cost_handler(costs: list, category: str, raw_amount: str, raw_date: str) -> str:
    if not validate_category(category):
        return UNKNOWN_COMMAND_MSG

    amount = parse_amount(raw_amount)
    if amount is None or amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    date = extract_date(raw_date)
    if date is None:
        return INCORRECT_DATE_MSG

    costs.append((amount, date))

    return OP_SUCCESS_MSG


def was_before(date1: tuple[int, int, int], date2: tuple[int, int, int]) -> bool:
    reverse_date_1 = (date1[2], date1[1], date1[0])
    reverse_date_2 = (date2[2], date2[1], date2[0])
    return reverse_date_1 <= reverse_date_2


def count_capital(incomes: list, costs: list, target_date: tuple[int, int, int]):
    total = 0.0
    for amount, date in incomes:
        if was_before(date, target_date):
            total += amount

    for cat, amount, date in costs:
        if was_before(date, target_date):
            total -= amount

    return total


def is_in_this_month(date: tuple[int, int, int], target: tuple[int, int, int]) -> bool:
    day, month, year = date
    day_target, month_target, year_target = target
    return year == year_target and month == month_target and day <= day_target


def count_stats(incomes: list, costs: list, target_date: tuple[int, int, int]):
    month_income = 0.0
    month_costs = {}

    for amount, date in incomes:
        if is_in_this_month(date, target_date):
            month_income += amount

    for category, amount, date in costs:
        if is_in_this_month(date, target_date):
            month_costs[category] = month_costs.get(category, 0) + amount

    return month_income, month_costs


def format_stats(
    raw_date: str,
    capital: float,
    month_income: float,
    month_costs: tuple[int, int, int],
):
    total_costs = sum(month_costs.values())

    profit = month_income - total_costs
    abs_profit = abs(profit)

    lines = []
    lines.append(f"Ваша статистика по состоянию на {raw_date}:")
    lines.append(f"Суммарный капитал: {capital:.2f} рублей")

    if profit >= 0:
        lines.append(f"В этом месяце прибыль составила {profit:.2f} рублей")
    else:
        lines.append("В этом месяце убыток составил {abs_profit:.2f} рублей")

    lines.append(f"Доходы: {month_income:.2f} рублей")
    lines.append(f"Расходы: {total_costs:.2f} рублей")

    lines.append("Детализация (категория: сумма):")

    for num, cat in enumerate(sorted(month_costs.keys()), start=1):
        lines.append(f"{num}. {cat}: {int(month_costs[cat])}")

    return "\n".join(lines)


def main() -> None:
    incomes = []
    costs = []

    while True:
        question = input().strip().split()
        command = question[0]

        if command == "income":
            if len(question) != 3:
                print(UNKNOWN_COMMAND_MSG)
                continue

            print(income_handler(incomes, question[1], question[2]))

        elif command == "cost":
            if len(question) != 4:
                print(UNKNOWN_COMMAND_MSG)
                continue

            print(cost_handler(costs, question[1], question[2], question[3]))

        elif command == "stats":
            if len(question) != 2:
                print(UNKNOWN_COMMAND_MSG)
                continue

            raw_date = question[1]
            date = extract_date(raw_date)
            if date is None:
                print(INCORRECT_DATE_MSG)
                continue

            capital = count_capital(incomes, costs, date)

            month_income, month_costs = count_stats(incomes, costs, date)

            print(format_stats(raw_date, capital, month_income, month_costs))

        else:
            print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()
