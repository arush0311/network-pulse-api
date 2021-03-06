"""Serialize the models"""
from rest_framework import serializers
from django.utils.encoding import smart_text
from django.core.exceptions import ObjectDoesNotExist
from pulseapi.entries.models import Entry, ModerationState
from pulseapi.tags.models import Tag
from pulseapi.issues.models import Issue
from pulseapi.creators.models import Creator
from pulseapi.users.models import EmailUser, UserBookmarks
from pulseapi.users.serializers import UserBookmarksSerializer

class CreatableSlugRelatedField(serializers.SlugRelatedField):
    """
    Override SlugRelatedField to create or update
    instead of getting upset that a tag doesn't exist
    """
    def to_internal_value(self, data):
        try:
            qs = self.get_queryset()
            return qs.get_or_create(**{self.slug_field: data})[0]
        except ObjectDoesNotExist:
            self.fail(
                'does_not_exist',
                slug_name=self.slug_field,
                value=smart_text(data)
            )
        except (TypeError, ValueError):
            self.fail('invalid')


class ModerationStateSerializer(serializers.ModelSerializer):
    class Meta:
        """
        Meta class. Because
        """
        model = ModerationState
        exclude = ()


class EntrySerializer(serializers.ModelSerializer):
    """
    Serializes an entry with embeded information including
    list of tags, categories and links associated with that entry
    as simple strings. It also includes a list of hyperlinks to events
    that are associated with this entry as well as hyperlinks to users
    that are involved with the entry
    """

    tags = CreatableSlugRelatedField(many=True,
                                     slug_field='name',
                                     queryset=Tag.objects,
                                     required=False)

    issues = serializers.SlugRelatedField(many=True,
                                          slug_field='name',
                                          queryset=Issue.objects,
                                          required=False)

    creators = CreatableSlugRelatedField(many=True,
                                         slug_field='name',
                                         queryset=Creator.objects,
                                         required=False)

    bookmark_count = serializers.SerializerMethodField()

    def get_bookmark_count(self, instance):
        """
        Get the total number of bookmarks this entry received
        """
        return instance.bookmarked_by.count()

    is_bookmarked = serializers.SerializerMethodField()

    def get_is_bookmarked(self, instance):
        """
        Check whether the current user has bookmarked this
        Entry. Anonymous users always see False
        """
        request = self.context['request']

        if hasattr(request, 'user'):
            user = request.user
            if user.is_authenticated():
                res = instance.bookmarked_by.filter(user=user)
                return res.count() > 0

        return False

    class Meta:
        """
        Meta class. Because
        """
        model = Entry
        exclude = ('internal_notes', 'published_by',)
