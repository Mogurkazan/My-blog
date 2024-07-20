import cloudinary
import cloudinary.uploader
import cloudinary.api

cloudinary.config(
  cloud_name = 'your_cloud_name',
  api_key = 'your_api_key',
  api_secret = 'your_api_secret'
)
