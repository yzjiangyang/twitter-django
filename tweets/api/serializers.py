from accounts.api.serializers import UserSerializerForTweet
from comments.api.serializers import CommentSerializer
from likes.api.serializers import LikeSerializer
from likes.services import LikeService
from random import randint
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from tweets.constants import TWEET_PHOTO_UPLOAD_LIMIT
from tweets.models import Tweet
from tweets.services import TweetService
from utils.redis.redis_helper import RedisHelper


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet(source='cached_user')
    has_liked = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    photo_urls = serializers.SerializerMethodField()

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'has_liked',
            'likes_count',
            'comments_count',
            'photo_urls',
        )

    def get_has_liked(self, obj):
        return LikeService.has_liked(self.context['request'].user, obj)

    def get_likes_count(self, obj):
        # randomly check if likes count is consistent
        if randint(0, 999) == 0:
            obj.refresh_from_db()
            actual_likes_count = obj.like_set.count()
            if obj.likes_count != actual_likes_count:
                obj.likes_count = actual_likes_count
                obj.save()
                return actual_likes_count

        return RedisHelper.get_count(obj, 'likes_count')

    def get_comments_count(self, obj):
        if randint(0, 999) == 0:
            obj.refresh_from_db()
            actual_comments_count = obj.comment_set.count()
            if obj.comments_count != actual_comments_count:
                obj.comments_count = actual_comments_count
                obj.save()
                return actual_comments_count

        return RedisHelper.get_count(obj, 'comments_count')

    def get_photo_urls(self, obj):
        photo_urls = []
        tweet_photos = obj.tweetphoto_set.all().order_by('order')
        for tweet_photo in tweet_photos:
            photo_urls.append(tweet_photo.file.url)
        return photo_urls


class TweetSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = Tweet
        fields = ('content', 'files')

    def validate(self, data):
        if len(data.get('files', [])) > TWEET_PHOTO_UPLOAD_LIMIT:
            raise ValidationError({
                'message': f'You can only upload {TWEET_PHOTO_UPLOAD_LIMIT} '
                'photos at most'
            })
        return data

    def create(self, validated_data):
        content = validated_data['content']
        user = self.context['request'].user
        tweet = Tweet.objects.create(user=user, content=content)
        if 'files' in validated_data:
            files = validated_data['files']
            TweetService.create_photos_from_files(tweet, files)

        return tweet


class TweetSerializerForDetail(TweetSerializer):
    comments = CommentSerializer(source='comment_set', many=True)
    likes = LikeSerializer(source='like_set', many=True)

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comments',
            'likes',
            'has_liked',
            'likes_count',
            'comments_count',
            'photo_urls',
        )
