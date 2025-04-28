# PutFileResponse

Response model for `PUT /v1/files/:file_path`.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**file_path** | **str** | The path of the file. | 
**message** | **str** | A message about the operation. | 

## Example

```python
from files_api_sdk.models.put_file_response import PutFileResponse

# TODO update the JSON string below
json = "{}"
# create an instance of PutFileResponse from a JSON string
put_file_response_instance = PutFileResponse.from_json(json)
# print the JSON string representation of the object
print PutFileResponse.to_json()

# convert the object into a dict
put_file_response_dict = put_file_response_instance.to_dict()
# create an instance of PutFileResponse from a dict
put_file_response_from_dict = PutFileResponse.from_dict(put_file_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


