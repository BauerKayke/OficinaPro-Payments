"""
DynamoDB Client para persistência de pagamentos.

Tech Challenge FIAP - Fase 4
Requisito: "Uso de pelo menos um banco não relacional (NoSQL)"

Este módulo substitui a persistência em PostgreSQL por DynamoDB,
atendendo ao requisito obrigatório de NoSQL da Fase 4.
"""

import boto3
import os
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List
from botocore.exceptions import ClientError
from botocore.config import Config

from app.logging_config import get_logger
from app.telemetry import get_tracer

logger = get_logger(__name__)
tracer = get_tracer(__name__)


class DynamoDBPaymentRepository:
    """
    Repositório de pagamentos usando DynamoDB.
    
    Tabela: oficinapro-payments
    Hash Key: payment_id (String)
    GSI: OrderIdIndex (order_id)
    """
    
    def __init__(self):
        """Inicializa conexão com DynamoDB."""
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.table_name = os.getenv("DYNAMODB_TABLE_NAME", "oficinapro-payments")
        
        config = Config(
            region_name=aws_region,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        self.dynamodb = boto3.resource('dynamodb', config=config)
        self.table = self.dynamodb.Table(self.table_name)
        
        logger.info("DynamoDB client initialized",
                   table=self.table_name,
                   region=aws_region)
    
    def create_payment(self, payment_data: Dict) -> Dict:
        """
        Cria um novo registro de pagamento no DynamoDB.
        
        Args:
            payment_data: Dados do pagamento
            
        Returns:
            Dict com payment_id e dados persistidos
        """
        with tracer.start_as_current_span("dynamodb.create_payment") as span:
            payment_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            item = {
                'payment_id': payment_id,
                'order_id': int(payment_data['order_id']),
                'amount': Decimal(str(payment_data['amount'])),
                'method': payment_data['method'],
                'status': payment_data.get('status', 'PENDING'),
                'transaction_id': payment_data.get('transaction_id', ''),
                'payer_email': payment_data['payer_email'],
                'description': payment_data.get('description', ''),
                'created_at': timestamp,
                'updated_at': timestamp,
                'success': payment_data.get('success', False),
                'message': payment_data.get('message', ''),
                'payment_url': payment_data.get('payment_url', ''),
                'qr_code': payment_data.get('qr_code', ''),
                'qr_code_base64': payment_data.get('qr_code_base64', ''),
                'barcode_content': payment_data.get('barcode_content', '')
            }
            
            try:
                self.table.put_item(Item=item)
                
                span.set_attribute("dynamodb.operation", "put_item")
                span.set_attribute("dynamodb.payment_id", payment_id)
                span.set_attribute("dynamodb.order_id", payment_data['order_id'])
                
                logger.info("Payment created in DynamoDB",
                           payment_id=payment_id,
                           order_id=payment_data['order_id'],
                           method=payment_data['method'],
                           status=item['status'])
                
                return item
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_msg = e.response['Error']['Message']
                
                span.set_attribute("error", True)
                span.set_attribute("dynamodb.error_code", error_code)
                
                logger.error("Failed to create payment in DynamoDB",
                            error=error_msg,
                            error_code=error_code,
                            payment_id=payment_id)
                raise
    
    def get_payment(self, payment_id: str) -> Optional[Dict]:
        """
        Busca um pagamento pelo ID.
        
        Args:
            payment_id: ID do pagamento
            
        Returns:
            Dict com dados do pagamento ou None
        """
        with tracer.start_as_current_span("dynamodb.get_payment") as span:
            span.set_attribute("dynamodb.payment_id", payment_id)
            
            try:
                response = self.table.get_item(Key={'payment_id': payment_id})
                
                if 'Item' in response:
                    logger.info("Payment found in DynamoDB",
                               payment_id=payment_id)
                    return response['Item']
                else:
                    logger.warning("Payment not found in DynamoDB",
                                  payment_id=payment_id)
                    return None
                    
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_msg = e.response['Error']['Message']
                
                span.set_attribute("error", True)
                span.set_attribute("dynamodb.error_code", error_code)
                
                logger.error("Failed to get payment from DynamoDB",
                            error=error_msg,
                            error_code=error_code,
                            payment_id=payment_id)
                raise
    
    def get_payments_by_order(self, order_id: int) -> List[Dict]:
        """
        Busca todos os pagamentos de uma ordem de serviço.
        
        Args:
            order_id: ID da ordem de serviço
            
        Returns:
            Lista de pagamentos
        """
        with tracer.start_as_current_span("dynamodb.get_payments_by_order") as span:
            span.set_attribute("dynamodb.order_id", order_id)
            
            try:
                response = self.table.query(
                    IndexName='OrderIdIndex',
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('order_id').eq(order_id)
                )
                
                items = response.get('Items', [])
                
                logger.info("Payments found for order",
                           order_id=order_id,
                           count=len(items))
                
                return items
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_msg = e.response['Error']['Message']
                
                span.set_attribute("error", True)
                span.set_attribute("dynamodb.error_code", error_code)
                
                logger.error("Failed to query payments by order",
                            error=error_msg,
                            error_code=error_code,
                            order_id=order_id)
                raise
    
    def update_payment_status(self, payment_id: str, status: str, 
                             transaction_id: Optional[str] = None) -> Dict:
        """
        Atualiza o status de um pagamento.
        
        Args:
            payment_id: ID do pagamento
            status: Novo status
            transaction_id: ID da transação (opcional)
            
        Returns:
            Dict com dados atualizados
        """
        with tracer.start_as_current_span("dynamodb.update_payment_status") as span:
            span.set_attribute("dynamodb.payment_id", payment_id)
            span.set_attribute("payment.new_status", status)
            
            update_expression = "SET #status = :status, updated_at = :updated_at"
            expression_values = {
                ':status': status,
                ':updated_at': datetime.utcnow().isoformat()
            }
            expression_names = {'#status': 'status'}
            
            if transaction_id:
                update_expression += ", transaction_id = :transaction_id"
                expression_values[':transaction_id'] = transaction_id
            
            try:
                response = self.table.update_item(
                    Key={'payment_id': payment_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values,
                    ExpressionAttributeNames=expression_names,
                    ReturnValues='ALL_NEW'
                )
                
                logger.info("Payment status updated in DynamoDB",
                           payment_id=payment_id,
                           new_status=status)
                
                return response['Attributes']
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_msg = e.response['Error']['Message']
                
                span.set_attribute("error", True)
                span.set_attribute("dynamodb.error_code", error_code)
                
                logger.error("Failed to update payment status",
                            error=error_msg,
                            error_code=error_code,
                            payment_id=payment_id)
                raise
    
    def list_payments(self, limit: int = 50) -> List[Dict]:
        """
        Lista pagamentos (scan).
        
        Args:
            limit: Número máximo de resultados
            
        Returns:
            Lista de pagamentos
        """
        with tracer.start_as_current_span("dynamodb.list_payments") as span:
            try:
                response = self.table.scan(Limit=limit)
                items = response.get('Items', [])
                
                logger.info("Payments listed from DynamoDB",
                           count=len(items))
                
                return items
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_msg = e.response['Error']['Message']
                
                span.set_attribute("error", True)
                span.set_attribute("dynamodb.error_code", error_code)
                
                logger.error("Failed to list payments",
                            error=error_msg,
                            error_code=error_code)
                raise
