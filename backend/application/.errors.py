from marshmallow import ValidationError

def validation_error_handler(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return {
            "error": "invalid request",
            "details": err.messages
        }, 400
    

__all__ = ["validation_error_handler"]
