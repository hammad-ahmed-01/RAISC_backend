from rest_framework import serializers
from .models import User, Profile

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['condition']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=User.USER_TYPES)
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'user_type', 'profile')

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        Profile.objects.update_or_create(user=user, defaults=profile_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'user_type', 'profile']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        instance = super(UserSerializer, self).update(instance, validated_data)
        Profile.objects.update_or_create(user=instance, defaults=profile_data)
        return instance
