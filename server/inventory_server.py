import json
import logging
from concurrent import futures

import grpc

from . import inventory_pb2
from . import inventory_pb2_grpc


logger = logging.getLogger()

INVENTORY_DATA: dict = json.load(open("data/mock_data_inventory.json"))


class InventoryServiceServicer(inventory_pb2_grpc.InventoryServiceServicer):
    def CheckAvailability(self, request, context):
        """
        Function to check the availability of the requested items.
        :param request: The request containing a map with the ids and the quantity.
        :param context: Request context.
        :return: The map with the ids and a bool if the requested quantity is available.
        """
        availability: dict = {}
        items: dict = request.items
        logger.info(f"Checking availability for products with ids {items.keys()}")

        for product_id, quantity in items.items():
            if INVENTORY_DATA.get(product_id, 0) >= quantity:
                availability[product_id] = True
                continue
            availability[product_id] = False

        return inventory_pb2.InventoryResponse(availability=availability)

    def ReserveItems(self, request, context):
        reserve_items: dict = request.items
        results: list = []
        overall_success: bool = True

        for product_id, quantity in reserve_items.items():
            logger.info(f"Reserving {quantity} pieces of the item {product_id}")
            available_quantity: int = INVENTORY_DATA.get(product_id, 0)

            if available_quantity >= quantity:
                INVENTORY_DATA[product_id] = available_quantity - quantity
                results.append(inventory_pb2.ReserveItemResult(
                    productId=product_id, success=True, message=f"Reserved {quantity} units"
                ))
                continue

            results.append(inventory_pb2.ReserveItemResult(
                productId=product_id, success=False, message=f"Not enough items in the inventory."
            ))
            overall_success = False

        return inventory_pb2.ReserveResponse(overallSuccess=overall_success, results=results)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(InventoryServiceServicer(), server)
    server.add_insecure_port("[::]:50051")
    print("Inventory Service running on port 50051...")

    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
