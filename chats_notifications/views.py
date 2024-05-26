from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from chats_notifications.utils import (
    save_image,
)


class ApplicationsChatsGenerateURLAPI(APIView):
    """
    API for generating image details to send in chat
    """

    def post(self, request):
        try:
            image, image_type, image_name, file_size = save_image(
                request.FILES["file"], path_req="ChatFiles/"
            )

            return Response(
                {
                    "file_url": image,
                    "file_type": image_type,
                    "file_name": image_name,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": "Something went wrong", "data": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
