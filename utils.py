import gtypes

#
# class ColorEnumMeta(enum.EnumMeta):
#     def __new__(mcs, name, bases, attrs):
#         groups = []
#         for attr in attrs.keys():
#             if attr.startswith('group_'):
#                 groups.append((attr.split('group_')[1], attrs[attr]))
#         obj = super().__new__(mcs, name, bases, attrs)
#
#         for m in obj:
#             for group_name, group in groups:
#                 setattr(m, group_name, m.name in getattr(obj, 'group_' + group_name)())
#         for m in obj:
#             for om in obj:
#                 setattr(m, om.name, m == om)
#         return obj
#
# class A(enum.Enum, metaclass=ColorEnumMeta):
#     x = "x", "X"
#     y = "y", "Y"
#     z = "z", "Z"
#
#     @classmethod
#     def group_one(cls):
#         return ["x", "y"]
#
# print(A.x.one)
# print(A.x.y)


def parse_type(x):
    if x == 'integer':
        return gtypes.IntegerType()
    if x == 'float':
        return gtypes.FloatType()
    if x == 'number':
        return gtypes.NumberType()
    if x == 'term':
        return gtypes.TermType()
    if x == 'any':
        return gtypes.AnyType()
    if type(x) == tuple:
        if len(x) >= 2 and x[-2] == '->':
            return gtypes.FunctionType([parse_type(y) for y in x[:-2]], parse_type(x[-1]))
        else:
            return gtypes.TupleType([parse_type(y) for y in x])
    if type(x) == dict:
        return gtypes.MapType({k: parse_type(x[k]) for k in x})
    if type(x) == list:
        if len(x) == 0:
            return gtypes.ElistType()
        if len(x) == 1:
            return gtypes.ListType(parse_type(x[0]))


def flatten(t):
    return [item for sublist in t for item in sublist]
