MOCK_RESPONSE = {
    "openapi": "3.1.0",
    "info": {
        "title": "FrameX",
        "version": "0.2.3",
    },
    "paths": {
        "/proxy/mock/get": {
            "get": {
                "tags": ["proxy"],
                "summary": "Proxy Mock Get",
                "operationId": "proxy_mock_get",
                "parameters": [
                    {
                        "name": "message",
                        "in": "query",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "title": "Message",
                        },
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
        "/proxy/mock/post": {
            "post": {
                "tags": ["proxy"],
                "summary": "Proxy Mock Post",
                "operationId": "proxy_mock_post",
                "parameters": [
                    {
                        "name": "message",
                        "in": "query",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "title": "Message",
                        },
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
        "/proxy/mock/post_model": {
            "post": {
                "tags": ["proxy"],
                "summary": "Proxy Mock Post Model",
                "operationId": "proxy_mock_post_model",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MockModel"}}},
                },
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
        "/proxy/mock/black_get": {
            "get": {
                "tags": ["proxy"],
                "summary": "Proxy Mock Get",
                "operationId": "proxy_mock_do_not_import",
                "parameters": [
                    {
                        "name": "message",
                        "in": "query",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "title": "Message",
                        },
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
        "/proxy/mock/black_post": {
            "post": {
                "tags": ["proxy"],
                "summary": "Proxy Mock Post",
                "operationId": "proxy_mock_black_post",
                "parameters": [
                    {
                        "name": "message",
                        "in": "query",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "title": "Message",
                        },
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
        "/api/v1/proxy/mock/info": {
            "get": {
                "tags": ["proxy"],
                "summary": "Proxy Mock Info",
                "operationId": "proxy_mock_info",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
        "/proxy/mock/auth/get": {
            "get": {
                "tags": ["proxy"],
                "summary": "Proxy Mock Get",
                "operationId": "proxy_mock_auth_get",
                "parameters": [
                    {
                        "name": "message",
                        "in": "query",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "title": "Message",
                        },
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
        "/proxy/mock/auth/sget": {
            "get": {
                "tags": ["proxy"],
                "summary": "Proxy Mock Get",
                "operationId": "proxy_mock_auth_sget",
                "parameters": [
                    {
                        "name": "message",
                        "in": "query",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "title": "Message",
                        },
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
    },
    "components": {
        "schemas": {
            "MockModel": {
                "title": "MockModel",
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {
                        "type": "integer",
                        "title": "Id",
                    },
                    "name": {
                        "type": "string",
                        "title": "Name",
                        "default": "default",
                    },
                },
            }
        }
    },
}
