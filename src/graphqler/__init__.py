from strawberry.fastapi import GraphQLRouter

# GraphQLRouter接收三个参数: schema, path, graphiql
# graphqler = GraphQLRouter(..., path="/", graphiql=True)
graphqler = GraphQLRouter(..., path="/gpl", graphql_ide="apollo-sandbox")
