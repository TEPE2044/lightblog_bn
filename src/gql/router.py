from strawberry.fastapi import GraphQLRouter
from .root import schema

gql_router = GraphQLRouter(
    schema,
    path="/gql",          # 最终 URL = /api/v1/gql
    graphiql=True
)