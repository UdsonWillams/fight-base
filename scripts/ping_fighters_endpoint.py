#!/usr/bin/env python3
import time
import argparse
import logging
import signal

try:
    import requests

    _HAS_REQUESTS = True
except Exception:
    import urllib.request as _urllib

    _HAS_REQUESTS = False


def fetch(url, timeout=10):
    if _HAS_REQUESTS:
        resp = requests.get(url, timeout=timeout)
        return resp.status_code, len(resp.content or b"")
    else:
        with _urllib.urlopen(url, timeout=timeout) as r:
            data = r.read()
            return r.getcode(), len(data or b"")


def main():
    default_url = (
        "https://fight-base-api.onrender.com/api/v1/fighters/"
        "?sort_by=overall&sort_order=desc&recent_activity=true&limit=50"
    )
    parser = argparse.ArgumentParser(description="Ping endpoint a cada intervalo")
    parser.add_argument("--url", default=default_url, help="Endpoint a ser pingado")
    parser.add_argument(
        "--interval", type=float, default=30.0, help="Intervalo em segundos"
    )
    parser.add_argument(
        "--duration",
        default=None,
        help="Duração total (ex: 30m, 1800s). Se omitido roda indefinidamente",
    )
    parser.add_argument(
        "--timeout", type=float, default=10.0, help="Timeout da requisição"
    )
    parser.add_argument("--log-level", default="INFO", help="Nível de log")
    args = parser.parse_args()

    def parse_duration(value):
        if value is None:
            return None
        v = str(value).strip().lower()
        try:
            if v.endswith("s"):
                return float(v[:-1])
            if v.endswith("m"):
                return float(v[:-1]) * 60.0
            if v.endswith("h"):
                return float(v[:-1]) * 3600.0
            return float(v)
        except Exception:
            raise argparse.ArgumentTypeError(
                "Formato inválido para --duration: %r" % value
            )

    duration_seconds = parse_duration(args.duration)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    stop = False

    def _handle(sig, frame):
        nonlocal stop
        logging.info("Signal recebido, finalizando...")
        stop = True

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)

    if duration_seconds:
        end_time = time.time() + duration_seconds
        logging.info(
            "Iniciando pings em %s a cada %ss por %ss (até %s)",
            args.url,
            args.interval,
            duration_seconds,
            time.ctime(end_time),
        )
    else:
        end_time = None
        logging.info(
            "Iniciando pings em %s a cada %ss (indefinido)", args.url, args.interval
        )

    while not stop and (end_time is None or time.time() < end_time):
        start = time.time()
        try:
            status, size = fetch(args.url, timeout=args.timeout)
            logging.info("Resposta: status=%s bytes=%d", status, size)
        except Exception as e:
            logging.exception("Falha na requisição: %s", e)
        elapsed = time.time() - start
        sleep = args.interval - elapsed
        if sleep > 0:
            time.sleep(sleep)

        if end_time and time.time() >= end_time:
            logging.info("Duração atingida: encerrando execução")
            break

    logging.info("Script finalizado")


if __name__ == "__main__":
    main()
