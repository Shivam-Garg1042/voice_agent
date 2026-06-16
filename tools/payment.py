"""
tools/payment.py
Payment tool stubs — no live integration yet.
When you're ready, replace the print statements with your
Razorpay / internal API calls.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def create_payment_request(
    driver_name: str,
    upi_id: str,
    amount: int,
) -> dict:
    """
    Stub: Create a payment request for a driver.
    Replace this with your actual Razorpay / payment API call.

    Args:
        driver_name: Name of the driver
        upi_id:      Driver's UPI ID e.g. "ramesh@upi"
        amount:      Amount in rupees

    Returns:
        dict with status and a fake payment link
    """
    logger.info(
        f"[Payment] REQUEST — Driver: {driver_name} | UPI: {upi_id} | "
        f"Amount: ₹{amount} | Time: {datetime.now()}"
    )

    # TODO: Replace with Razorpay API call
    # import razorpay
    # client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))
    # link = client.payment_link.create({...})

    return {
        "status": "pending",
        "driver_name": driver_name,
        "upi_id": upi_id,
        "amount": amount,
        "payment_link": f"https://pay.chargeup.in/stub/{driver_name.lower()}-{amount}",
        "created_at": datetime.now().isoformat(),
    }


async def log_payment_promise(
    driver_name: str,
    promised_date: str,
    amount: int,
    reason: str = "",
) -> dict:
    """
    Stub: Log a promise-to-pay from the driver.
    Replace with your CRM API call.

    Args:
        driver_name:   Driver's name
        promised_date: Date driver promised to pay e.g. "kal subah"
        amount:        Promised amount in rupees
        reason:        Reason for delay if provided
    """
    logger.info(
        f"[Payment] PROMISE — Driver: {driver_name} | By: {promised_date} | "
        f"Amount: ₹{amount} | Reason: {reason} | Time: {datetime.now()}"
    )

    # TODO: Write to your CRM / database

    return {
        "status": "promise_logged",
        "driver_name": driver_name,
        "promised_date": promised_date,
        "amount": amount,
    }
