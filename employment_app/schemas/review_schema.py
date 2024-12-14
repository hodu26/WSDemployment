from marshmallow import Schema, fields, validate

class ReviewSchema(Schema):
    company_id = fields.Int(required=True, description='리뷰할 회사 id', example=100)
    rating = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=5, error="평점은 1에서 5 사이여야 합니다."),
        description='평점',
        example=4
    )
    review_text = fields.Str(description='리뷰 내용', example="좋은 회사입니다!")

class ReviewCompanyIdSchema(Schema):
    company_id = fields.Int(description="회사 ID", example=100)