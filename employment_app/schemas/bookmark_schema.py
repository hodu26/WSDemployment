from marshmallow import Schema, fields, validate

class BookmarkSchema(Schema):
    job_post_id = fields.Int(required=True, description="북마크하려는 채용 공고의 ID", example=100)

class BookmarkListSchema(Schema):
    page = fields.Int(missing=1, description="페이지 번호", example=1)
    sort = fields.Str(
        example="desc",
        missing='desc',
        validate=validate.OneOf(
            ['desc', 'asc']
        ),
        description='날짜별 정렬'
    )