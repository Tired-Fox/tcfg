from tcfg.type_check import type_check, GreaterThan, LessThan, Range, MISSING, PathType

if __name__ == "__main__":
    # Da' Rules
    # - Unions match any argument
    # - Optional matches one argument or NoneType
    # - Generics have there __args__ compared.
    #     - If named tuple and is GenericAlias then is certain length and each index is compared
    #     - If form of dict then compares key and value
    #     - If named list then all children must match inner type
    #     - If named set then all children must be unique and match inner type
    # - If type then just compare
    # - If PathType then compare if path exists and format string

    # print(type_check(int, 3))
    # print(type_check(PathType[True], "./type_checking.py"))
    # print(type_check(list[int], [2]))
    # print(type_check(tuple[int, int], [3]))
    # print(type_check(set[int], [3, 5, 6, 6]))
    # print(type_check(dict[str, str], {"valid": "valid"}))
    # print(type_check(Option["Dog", "Cat", 3], MISSING))
    # print(type_check(Optional[int], None))
    # print(type_check(int | None, "Invalid"))
    # print(type_check(Any, "Invalid"))
    # print(ct_value(GreaterThan(3)))
    # print(ct_validate(GreaterThan[1], MISSING))
    # print(ct_validate(LessThan[10], 9))
    # print(ct_validate(Range[0, 10], 5))
    print(type_check(PathType[True], "./type_checking.py"))
