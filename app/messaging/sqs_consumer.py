"""
SQS Consumer para Payment Service
Consome mensagens de comandos de pagamento via SQS
"""

import boto3
import json
import os
from typing import Dict, Any
from app.logging_config import get_logger
from app.telemetry import get_tracer

logger = get_logger(__name__)
tracer = get_tracer(__name__)


class SQSPaymentConsumer:
    """Consumer para processar comandos de pagamento via SQS"""
    
    def __init__(self):
        self.sqs = boto3.client('sqs', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.queue_url = os.getenv('SQS_PAYMENT_COMMANDS_QUEUE')
        self.running = True
        
        if not self.queue_url:
            logger.warning("SQS_PAYMENT_COMMANDS_QUEUE não configurada - Consumer desabilitado")
    
    def start_consuming(self):
        """Inicia o loop de consumo de mensagens"""
        if not self.queue_url:
            logger.info("SQS Consumer desabilitado - queue_url não configurada")
            return
        
        logger.info(f"SQS Consumer iniciado - Queue: {self.queue_url}")
        
        while self.running:
            try:
                # Long polling (20 segundos)
                response = self.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20,
                    MessageAttributeNames=['All'],
                    AttributeNames=['All']
                )
                
                messages = response.get('Messages', [])
                
                if messages:
                    logger.info(f"Recebidas {len(messages)} mensagens da fila SQS")
                    
                    for message in messages:
                        self._process_message(message)
                        
            except Exception as e:
                logger.error(f"Erro ao consumir mensagens SQS: {e}", exc_info=True)
                # Espera 5 segundos antes de tentar novamente
                import time
                time.sleep(5)
    
    def _process_message(self, message: Dict[str, Any]):
        """Processa uma mensagem individual"""
        receipt_handle = message.get('ReceiptHandle')
        message_id = message.get('MessageId')
        
        with tracer.start_as_current_span("sqs_process_message") as span:
            span.set_attribute("message.id", message_id)
            
            try:
                # Parse message body
                body = json.loads(message['Body'])
                
                # Obter tipo de comando das attributes
                command_type = message.get('MessageAttributes', {}).get('command-type', {}).get('StringValue', 'Unknown')
                span.set_attribute("command.type", command_type)
                
                logger.info(
                    "Processando comando SQS",
                    command_type=command_type,
                    message_id=message_id,
                    body=body
                )
                
                # Processar comando baseado no tipo
                self._handle_command(command_type, body)
                
                # Deletar mensagem após processamento bem-sucedido
                self.sqs.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )
                
                logger.info(
                    "Comando processado com sucesso",
                    command_type=command_type,
                    message_id=message_id
                )
                
            except Exception as e:
                logger.error(
                    f"Erro ao processar mensagem {message_id}: {e}",
                    exc_info=True,
                    message_id=message_id
                )
                span.set_status("error")
                span.set_attribute("error.message", str(e))
                # Não deleta a mensagem em caso de erro - voltará para fila
    
    def _handle_command(self, command_type: str, body: Dict[str, Any]):
        """Despacha comando para o handler apropriado"""
        
        if command_type == 'ProcessPayment':
            self._process_payment_command(body)
        elif command_type == 'RefundPayment':
            self._process_refund_command(body)
        else:
            logger.warning(f"Tipo de comando desconhecido: {command_type}")
    
    def _process_payment_command(self, body: Dict[str, Any]):
        """Processa comando de pagamento"""
        from app.services.payment_service import PaymentService
        from app.schemas import PaymentRequest
        
        # Converter body para PaymentRequest
        payment_request = PaymentRequest(**body)
        
        # Processar pagamento
        payment_service = PaymentService()
        result = payment_service.process_payment(payment_request)
        
        # Publicar evento de resultado (opcional)
        from app.messaging.sqs_publisher import SQSPaymentPublisher
        publisher = SQSPaymentPublisher()
        publisher.publish_payment_processed(result)
        
        logger.info(f"Pagamento processado: {result.transaction_id}")
    
    def _process_refund_command(self, body: Dict[str, Any]):
        """Processa comando de estorno"""
        from app.services.payment_service import PaymentService
        from app.schemas import RefundRequest
        
        # Converter body para RefundRequest
        refund_request = RefundRequest(**body)
        
        # Processar estorno
        payment_service = PaymentService()
        result = payment_service.refund_payment(refund_request)
        
        # Publicar evento de resultado
        from app.messaging.sqs_publisher import SQSPaymentPublisher
        publisher = SQSPaymentPublisher()
        publisher.publish_refund_processed(result)
        
        logger.info(f"Estorno processado: {result.transaction_id}")
    
    def stop(self):
        """Para o loop de consumo"""
        self.running = False
        logger.info("SQS Consumer parando...")
