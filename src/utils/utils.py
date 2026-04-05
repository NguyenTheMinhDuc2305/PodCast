def extract_structure(data: dict):
    # This function extract each sentences from the paragraph
    id = 0
    result = {}
    for key, value in data.items():
        for item in value.split(""):

            result[id] = {
                "title": key,
                "content": item
            }
            id += 1
    return result

