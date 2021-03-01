from gen import *
from tokentypes import *
from sym import *
from error import *


class Compiler(object):
    def __init__(self, outfn):
        self.error = 0

        self.codegen = CodeGenerator(outfn)
        self.codegen.generate_beginning()

    def close_output_file(self):
        self.codegen.close_file()

    def visit(self, node, context):
        func = getattr(self, "visit_{}".format(type(node).__name__), self.no_visit_method)
        return func(node, context)

    def visit_GlobalStatements(self, stmts, context):
        for stmt in stmts:
            self.visit(stmt, context)
            if self.error:
                return

    def visit_FunctionDeclarationNode(self, node, context):
        s = Symbol(node.name.value, A_FUNCTION, self.get_data_type(node.type.value))
        context.add_symbol(s)

        new_context = FunctionContext(node.name.value, context)

        self.codegen.gen_function_beginning(node.name.value)

        for stmt in node.stmts:
            self.visit(stmt, new_context)
            if self.error:
                return

        self.codegen.gen_function_end()

        context = new_context.close_context()

        return NO_REG, D_NULL

    def visit_GlobalVarDeclarationNode(self, node, context):
        s = Symbol(node.name.value, A_VARIABLE, self.get_data_type(node.type.value))
        context.add_symbol(s)

        self.codegen.gen_decl_global_var(s.data_type, s.name)
    
    def visit_VarAssignNode(self, node, context):
        s = context.get_symbol(node.name.value.value)
        
        if not s:
            self.error = 1
            err = Error("Variable {} is not defined.".format(s.name), node.pos_start, node.pos_end)
            print(err.as_string())
            return NO_REG, D_NULL

        r, t = self.visit(node.expr, context)

        if (s.is_global):
            self.codegen.gen_assign_global_var(s.data_type, s.name, r)
        else:
            # self.codegen.get_assign_local_var(s.data_type, s.name, r)
            pass
        
    def visit_IntLitNode(self, node, context):
        return self.codegen.load_int(node.value), D_INT

    def visit_IdentifierNode(self, node, context):
        s = context.get_symbol(node.value.value)
        
        if not s:
            self.error = 1
            err = Error("Variable {} is not defined.".format(node.value.value), node.pos_start, node.pos_end)
            print(err.as_string())
            return NO_REG, D_NULL
        
        if s.is_global:
            return self.codegen.gen_load_global_var(s.data_type, s.name), s.data_type

    def visit_UnaryOperationNode(self, node, context):
        if node.sign == T_MINUS:
            r1 = self.codegen.load_int(0)
            r2, t = self.visit(node.right_node, context)

            if (t == D_INT): # or other types that support '-'
                return self.codegen.sub_int(r1, r2), t

    def visit_BinaryOperationNode(self, node, context):
        r1, t1 = self.visit(node.left_node, context)
        r2, t2 = self.visit(node.right_node, context)

        if not (t1 == t2):
            self.error = 1
            err = Error("You can't execute a binary operation between {} and {}".format(v_names[t1], v_names[t2]), node.pos_start, node.pos_end)
            print(err.as_string())
            return NO_REG, D_NULL

        if t1 == D_INT:
            if node.sign == T_PLUS:
                return self.codegen.add_int(r1, r2), D_INT
            elif node.sign == T_MINUS:
                return self.codegen.sub_int(r1, r2), D_INT
            elif node.sign == T_ASTERISK:
                return self.codegen.mul_int(r1, r2), D_INT
            elif node.sign == T_SLASH:
                return self.codegen.div_int(r1, r2), D_INT
        
        self.error = 1
        err = Error("Type {} does not support binary operations".format(v_names[t1]), node.pos_start, node.pos_end)
        print(err.as_string())
        return NO_REG, D_NULL

    def visit_PrintNode(self, node, context):
        r1, t = self.visit(node.expr, context)
        
        if t == D_INT:
            self.codegen.print_int(r1)
        
        return NO_REG, None

    @staticmethod
    def get_data_type_by_node(node):
        if type(node).__name__ == "IntLitNode":
            return D_INT
        elif type(node).__name__ == "NullNode":
            return D_NULL
        else:
            return -1
        
    def get_data_type(self, n):
        if n == 'int':
            return D_INT
        else:
            return -1

    def no_visit_method(self, node, context):
        raise Exception("No visit method defined for {}".format(type(node).__name__))