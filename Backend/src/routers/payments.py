"""
Módulo de Roteamento para Pagamentos com Stripe.

Define os endpoints para iniciar uma sessão de pagamento e para receber
notificações (webhooks) do Stripe, que confirmam o status das transações.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
import logging
import stripe
from stripe import StripeError, SignatureVerificationError
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy.orm import Session
from stripe.checkout import Session as StripeSession

from .. import crud
from ..database import get_db
from ..settings import settings

# -------------------------------------------------------------------------- #
#                             CONFIGURAÇÃO INICIAL                           #
# -------------------------------------------------------------------------- #
stripe.api_key = settings.STRIPE_SECRET_KEY
router = APIRouter(prefix="/payments", tags=["Payments"])


# -------------------------------------------------------------------------- #
#                 ENDPOINT DE CRIAÇÃO DE SESSÃO DE CHECKOUT                  #
# -------------------------------------------------------------------------- #
@router.post("/create-checkout-session/{order_id}", status_code=status.HTTP_200_OK)
async def create_checkout_session(order_id: int, db: Session = Depends(get_db)):
    """
    Cria uma Sessão de Checkout no Stripe para um pedido existente.
    """
    order = crud.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "paid":
        raise HTTPException(status_code=400, detail="Order has already been paid.")

    line_items = []
    for item in order.items:
        line_items.append(
            {
                "price_data": {
                    "currency": "brl",
                    "product_data": {
                        "name": item.product.name
                        if item.product
                        else "Produto Removido"
                    },
                    "unit_amount": int(item.price_at_purchase * 100),
                },
                "quantity": item.quantity,
            }
        )

    try:
        checkout_session: StripeSession = stripe.checkout.Session.create(
            line_items=line_items,
            mode="payment",
            success_url=f"{settings.CLIENT_URL}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.CLIENT_URL}/payment-cancelled",
            metadata={"order_id": str(order.id)},
        )

        if not checkout_session.url:
            raise HTTPException(
                status_code=500, detail="Stripe did not return a checkout URL."
            )

        payment_intent_id = checkout_session.payment_intent
        if isinstance(payment_intent_id, str):
            order.payment_intent_id = payment_intent_id
            db.commit()

        return {"checkout_url": checkout_session.url}

    except StripeError as e:
        raise HTTPException(
            status_code=400, detail=f"Stripe error: {e.user_message or str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


# -------------------------------------------------------------------------- #
#                       ENDPOINT DE WEBHOOK DO STRIPE                        #
# -------------------------------------------------------------------------- #
@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Processa eventos (webhooks) do Stripe de forma segura.
    """
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")
    except SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_id_str = session.get("metadata", {}).get("order_id")

        if not order_id_str:
            logging.error("Webhook 'checkout.session.completed' recebido sem order_id.")
            return {"status": "success", "detail": "Webhook ignored, no order_id."}
        try:
            order = crud.get_order_by_id(db, int(order_id_str))
            if (
                order
                and order.status != "paid"
                and session.get("payment_status") == "paid"
            ):
                order.status = "paid"
                order.payment_intent_id = session.get("payment_intent")
                db.commit()
                logging.info(
                    f"Pedido #{order_id_str} atualizado para 'paid' via webhook."
                )
        except Exception as e:
            logging.error(
                f"Erro de DB ao processar webhook para order_id {order_id_str}: {e}"
            )
            raise HTTPException(
                status_code=500,
                detail="Database processing failed. Webhook will be retried.",
            )

    return {"status": "success"}
