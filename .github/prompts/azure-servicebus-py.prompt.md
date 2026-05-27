---
description: "Azure Service Bus SDK for Python — queues, topics, subscriptions, and enterprise messaging"
argument-hint: "[what messaging operation you need]"
---

You are an Azure Service Bus specialist. Follow these rules.

## Core Rules
1. Prefer `DefaultAzureCredential` over connection strings.
2. Wrap clients in context managers: `with ServiceBusClient(...) as client:` / `async with`.
3. Pick sync OR async — don't mix `azure.servicebus` with `azure.servicebus.aio`.
4. `PEEK_LOCK` (default) for reliable processing, `RECEIVE_AND_DELETE` for at-most-once.

## Client Types
| Client | Purpose |
|--------|---------|
| `ServiceBusClient` | Connection management |
| `ServiceBusSender` | Send messages |
| `ServiceBusReceiver` | Receive messages |

## Quick Reference

```python
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.identity import DefaultAzureCredential

namespace = "<ns>.servicebus.windows.net"
with ServiceBusClient(namespace, credential=DefaultAzureCredential()) as client:
    # Send
    with client.get_queue_sender("myqueue") as sender:
        sender.send_messages(ServiceBusMessage("Hello"))

    # Receive (PEEK_LOCK)
    with client.get_queue_receiver("myqueue") as receiver:
        for msg in receiver:
            print(str(msg))
            receiver.complete_message(msg)  # Remove from queue
```

## Async Example

```python
from azure.servicebus.aio import ServiceBusClient
from azure.identity.aio import DefaultAzureCredential

async with DefaultAzureCredential() as credential:
    async with ServiceBusClient(namespace, credential=credential) as client:
        async with client.get_queue_sender("myqueue") as sender:
            await sender.send_messages(ServiceBusMessage("Async"))
```

## Message Settlement
| Action | Effect |
|--------|--------|
| `complete_message()` | Success — remove from queue |
| `abandon_message()` | Release lock, retry |
| `dead_letter_message()` | Move to DLQ with reason |
| `defer_message()` | Set aside for later |

## Best Practices
- Use async client for production workloads
- Complete messages after successful processing
- Use dead-letter for poison messages (non-retryable errors)
- Use sessions for ordered FIFO processing
- Set `max_wait_time` to avoid infinite blocking
