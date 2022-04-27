import Parser as p

class Arg_Type():
    """
    self.type is None unless it is a recursive type (ie array of array)
    type_str is the string of the type
    type_width is 0 for scalar instructions, vector width if vector
    for multilevel arrays, 
    is_pointer is for if the entire thing is a pointer,
    is_arr_pointer is for if it is an array of pointers
        not sure if this is necessary but its implemented
    """
    def __init__(self):
        self.recurse_type = None
        self.type_str = 'DEFAULT'
        self.width = 0
        self.is_pointer = False
        self.is_vector = False
        self.is_arr_pointer = False
    #Gets the type of the type starting at idx in tokens
    #returns the index of the last element of the types
    def Get_Type(self, tokens, idx):
        if(tokens[idx] not in p.Instruction.type_tokens):
            print("Error, attempting to get type on bad index")
        if(tokens[idx] == '<'):
            self.is_vector = True
            self.width = int(tokens[idx + 1])
            self.type_str = tokens[idx + 3]
            idx += 4
            if(tokens[idx] == '*'):
                self.is_arr_pointer = True
                idx += 1
        elif(tokens[idx] == '['):
            self.width = int(tokens[idx + 1])
            #if it is a recursive type
            if(tokens[idx + 3] == '<' or tokens[idx + 3] == '['):
                self.recurse_type = Arg_Type()
                idx = self.recurse_type.Get_Type(tokens, idx + 3)
                self.type_str = "Array"
                idx += 1 #add one bc the ] will add up
                if(tokens[idx] == '*'):
                    self.is_arr_pointer = True
                    idx += 1
            else:
                self.type_str = tokens[idx + 3]
                idx += 4
                if(tokens[idx] == '*'):
                    self.is_arr_pointer = True
                    idx += 1
        else:
            self.type_str = tokens[idx]
        if(idx + 1 < len(tokens)):
            if(tokens[idx + 1] == '*'):
                self.is_pointer = True
                idx += 1
        return idx
    
    #only prints if do_print = true
    #otherwise just returns a string
    def printType(self, do_print=False):
        
        print_str = ""
        pointer_str = ""
        arr_pointer_str = ""
        if(self.is_pointer):
            pointer_str = '*'
        if(self.is_arr_pointer):
            arr_pointer_str = '*'
        if(self.recurse_type is not None):
            print_str = '[' + str(self.width) + ' x ' + self.recurse_type.printType() + arr_pointer_str + ']'
        elif(self.width > 0):
            bracket1 = '['
            bracket2 = ']'
            if(self.is_vector):
                bracket1 = '<'
                bracket2 = '>'
            print_str = bracket1 + str(self.width) + ' x ' + self.type_str + arr_pointer_str + bracket2
        else:
            print_str = self.type_str
        print_str += pointer_str
        if(do_print):
            print(print_str)
        return print_str

#cannot 
class Fn_Type(Arg_Type):
    """
    holds the arguments for a function type.
    has
        return type
        function flags
        function name
        function arguments -- of type Instruction type (from function name)
    """
    def __init__(self):
        self.function_name = "DEFAULT"
        self.flags = []
        self.args = 0
    