from rest_framework import serializers


class ChatHistoryItemSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['user', 'assistant'])
    content = serializers.CharField(max_length=4000, allow_blank=False)


class AdvisorChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000, allow_blank=False)
    history = ChatHistoryItemSerializer(many=True, required=False, default=list)

    def validate_history(self, value):
        return value[-12:]


class AdvisorProgramSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    direction = serializers.CharField(required=False, allow_blank=True)
    program_type = serializers.CharField(required=False, allow_blank=True)
    program_type_label = serializers.CharField(required=False, allow_blank=True)
    learning_format = serializers.CharField(required=False, allow_blank=True)
    hours_volume = serializers.IntegerField(required=False)
    duration = serializers.CharField(required=False, allow_blank=True)
    cost = serializers.CharField(required=False, allow_blank=True)
    lead = serializers.CharField(required=False, allow_blank=True)
    target_audience = serializers.CharField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True)


class AdvisorChatResponseSerializer(serializers.Serializer):
    reply = serializers.CharField()
    programs = AdvisorProgramSerializer(many=True)
