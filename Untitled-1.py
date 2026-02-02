class Order:
    def __init__(self, order_id, customer_name):
        self.order_id = order_id
        self.customer_name = customer_name
        self.next = None

class OrderQueue:
    def __init__(self):
        self.front = self.rear = None

    def add_order(self, order_id, customer_name):
        new_order = Order(order_id, customer_name)
        if not self.rear:
            self.front = self.rear = new_order
        else:
            self.rear.next = new_order
            self.rear = new_order
        print(f"Order {order_id} added.")

    def cancel_order(self, order_id):
        current = self.front
        previous = None

        while current:
            if current.order_id == order_id:
                if previous:
                    previous.next = current.next
                else:
                    self.front = current.next

                if current == self.rear:
                    self.rear = previous

                print(f"Order {order_id} canceled.")
                return
            previous = current
            current = current.next

        print(f"Order {order_id} not found.")

    def display_orders(self):
        current = self.front
        if not current:
            print("No pending orders.")
            return

        print("Pending Orders:")
        while current:
            print(f"Order ID: {current.order_id}, Customer: {current.customer_name}")
            current = current.next

# Example Usage
queue = OrderQueue()
queue.add_order(101, "Alice")
queue.add_order(102, "Bob")
queue.display_orders()
queue.cancel_order(102)
queue.display_orders()