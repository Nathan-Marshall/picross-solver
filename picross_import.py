def picross_import(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()

    result = []
    for line in lines:
        # Ignore the dimensions and title
        data = line.split('\t')[2:]

        # Split on the dash
        for d in data:
            sections = d.split('-')

            # Split on the colons and the commas
            arrays = [[[int(num) for num in item.split(',')] for item in sec.split(':')] for sec in sections]
            result.append(arrays)

    return result
