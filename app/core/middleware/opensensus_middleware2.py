import logging
import os
from opencensus.trace import config_integration
from opencensus.ext.azure.log_exporter import AzureLogHandler
 

from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES

from starlette.requests import Request
from starlette.responses import Response
from starlette.responses import JSONResponse

appinsight_conn=os.getenv("APPINSIGHT_CONN")
HTTP_URL = COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = COMMON_ATTRIBUTES['HTTP_STATUS_CODE']
logger = logging.getLogger(__name__)
config_integration.trace_integrations(["logging", "requests", "sqlalchemy", "postgresql"])
 
handler = AzureLogHandler(
    connection_string=appinsight_conn
)
handler.setFormatter(logging.Formatter("%(traceId)s %(spanId)s %(message)s"))
logger.addHandler(handler)

async def middlewareOpencensus(request: Request, call_next):
    tracer = Tracer(
        exporter=AzureExporter(
            connection_string=appinsight_conn
        ),
        sampler=ProbabilitySampler(1.0),
    )
    with tracer.span("main") as span:
        span.span_kind = SpanKind.SERVER
 
        response = await call_next(request)
 
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_STATUS_CODE, attribute_value=response.status_code
        )
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_URL, attribute_value=str(request.url)
        )
 
    return response