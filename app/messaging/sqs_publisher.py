"""
SQS Publisher para Payment Service
Publica eventos de resultado de pagamento via SQS
"""

import boto3
import json
import os
from datetime import datetime
from typing import Dict, Any
from app.logging_config import get_logger
from app.schemas import PaymentResponse, RefundResponse

logger = get_logger(__name__)


class SQSPaymentPublisher:
    """Publisher para publicar eventos de pagamento via SQS"""
    
    def __init__(self):
        self.sqs = boto3.client('sqs', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.events_queue = os.getenv('SQS_PAYMENT_EVENTS_QUEUE')
        
        if not self.events_queue:
            logger.warning("SQS_PAYMENT_EVENTS_QUEUE não configurada - Publisher desabilitado")
    
    def publish_payment_processed(self, payment_response: PaymentResponse):
        """Publica evento de pagamento processado"""
        if not self.events_queue:
            logger.debug("Publisher desabilitado - queue não configurada")
            return
        
        try:
            event = {
                "event_type": "PaymentProcessed",
                "event_id": f"evt_{payment_response.transaction_id}",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "transaction_id": payment_response.transaction_id,
                    "status": payment_response.status,
                    "success": payment_response.success,
                    "amount": payment_response.amount,
                    "currency": payment_response.currency,
                    "payment_method": payment_response.payment_method,
                    "message": payment_response.message
                }
            }
            
            message_body = json.dumps(event, default=str)
            
            response = self.sqs.send_message(
                QueueUrl=self.events_queue,
                MessageBody=message_body,
                MessageAttributes={
                    'event-type': {
                        'StringValue': 'PaymentProcessed',
                        'DataType': 'String'
                    },
                    'transaction-id': {
                        'StringValue': payment_response.transaction_id,
                        'DataType': 'String'
                    }
                }
            )
            
            logger.info(
                "Evento PaymentProcessed publicado",
                event_id=event['event_id'],
                transaction_id=payment_response.transaction_id,
                message_id=response.get('MessageId')
            )
            
        except Exception as e:
            logger.error(
                f"Erro ao publicar evento PaymentProcessed: {e}",
                exc_info=True,
                transaction_id=payment_response.transaction_id
            )
    
    def publish_refund_processed(self, refund_response: RefundResponse):
        """Publica evento de estorno processado"""
        if not self.events_queue:
            logger.debug("Publisher desabilitado - queue não configurada")
            return
        
        try:
            event = {
                "event_type": "RefundProcessed",
                "event_id": f"evt_{refund_response.refund_id}",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "refund_id": refund_response.refund_id,
                    "original_transaction_id": refund_response.original_transaction_id,
                    "status": refund_response.status,
                    "success": refund_response.success,
                    "refunded_amount": refund_response.refunded_amount,
                    "currency": refund_response.currency,
                    "message": refund_response.message
                }
            }
            
            message_body = json.dumps(event, default=str)
            
            response = self.sqs.send_message(
                QueueUrl=self.events_queue,
                MessageBody=message_body,
                MessageAttributes={
                    'event-type': {
                        'StringValue': 'RefundProcessed',
                        'DataType': 'String'
                    },
                    'refund-id': {
                        'StringValue': refund_response.refund_id,
                        'DataType': 'String'
                    },
                    'transaction-id': {
                        'StringValue': refund_response.original_transaction_id,
                        'DataType': 'String'
                    }
                }
            )
            
            logger.info(
                "Evento RefundProcessed publicado",
                event_id=event['event_id'],
                refund_id=refund_response.refund_id,
                message_id=response.get('MessageId')
            )
            
        except Exception as e:
            logger.error(
                f"Erro ao publicar evento RefundProcessed: {e}",
                exc_info=True,
                refund_id=refund_response.refund_id
            )
