def picross_import(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()

    result = []
    for line in lines:
        # Ignore the dimensions and title
        data = line[max(line.rfind('\t'), line.rfind(' ')) + 1:]

        # Split on the dash
        sections = data.split('-')

        # Split on the colons and the commas
        arrays = [[[int(num) for num in item.split(',')] for item in sec.split(':')] for sec in sections]
        result.append(arrays)

    return result
