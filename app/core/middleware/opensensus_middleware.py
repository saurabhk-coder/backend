# Opencensus imports
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES


from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from starlette.responses import JSONResponse

HTTP_URL = COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = COMMON_ATTRIBUTES['HTTP_STATUS_CODE']
appinsight_conn="InstrumentationKey=28338f74-7cb7-409c-b458-c55499fff01a;IngestionEndpoint=https://centralindia-0.in.applicationinsights.azure.com/;LiveEndpoint=https://centralindia.livediagnostics.monitor.azure.com/"
exporter=AzureExporter(connection_string=appinsight_conn)
sampler=ProbabilitySampler(1.0)

async def add_opensense(request: Request, call_next):  
    tracer = Tracer(exporter=exporter, sampler=sampler)       
    with tracer.span("main") as span:
        span.span_kind = SpanKind.SERVER

        response = await call_next(request)

        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_STATUS_CODE,
            attribute_value=response.status_code)
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_URL,
            attribute_value=str(request.url))

    return response


# async def catch_exceptions_middleware(request: Request, call_next):
#     try:
#         return await call_next(request)
#     except Exception as e:
#         return JSONResponse({"error": str(e)}, status_code=500, )
