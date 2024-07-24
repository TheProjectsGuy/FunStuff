# Calculate the EMI payments on a debt
"""
    Reference
    - https://emicalculator.net/
"""

# %%
loan_amount = 1e7
yearly_interest = 8.5/100
loan_tenure_years = 5

# %%
def get_emi(loan_amount, yearly_interest, loan_tenure_years):
    r = (1 + (yearly_interest / 12))
    p = loan_amount
    n = loan_tenure_years * 12
    emi = (p * r ** n * (r - 1)) / (r ** n - 1)
    return emi


# %%
# Loan specifications
num_payments = loan_tenure_years * 12
monthly_interest = yearly_interest / 12
# Payment process
emi = get_emi(loan_amount, yearly_interest, loan_tenure_years)
principal_paid = 0
interest_paid = 0
left_amount = loan_amount
all_payments = []   # (yr, mo, int_part, p_paid, emi, p_left)
for i in range(num_payments):
    interest = left_amount * monthly_interest
    principal_amount = emi - interest
    principal_left = left_amount - principal_amount
    all_payments.append((i // 12, i % 12, interest, 
                    principal_amount,principal_left))
    left_amount = principal_left
    interest_paid += interest
    principal_paid += principal_amount


# %%
print(f"{'SNo':>5s} {'Yr':>3s} {'Mo':>3s} {'Int':>10s} "\
        f"{'Pr':>10s} {'T Paid':>12s} {'Left':>12s}")
tp = 0
i = 0
for y, m, int_part, p_paid, p_left in all_payments:
    tp += emi
    i += 1
    print(f"{i:>4d}> {y:>3d} {m:>3d} " \
            f"{int_part:>10.2f} {p_paid:>10.2f} "\
            f"{tp:>12.2f} {p_left:>12.2f}")

print(f"Loan Amount: {loan_amount:.2f}")
print(f"Yearly interest: {yearly_interest*100:.2f}%")
print(f"Loan Tenure: {loan_tenure_years} years")
print(f"Monthly EMI: {emi:.2f}")
print(f"Total Interest Paid: {interest_paid:.2f}")

# %%
