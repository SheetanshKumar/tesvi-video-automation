class Question:

    def __init__(self,QuestionId, QuestionNumber, QuestionText, Options, AnswerKeys, Timer,
                   Hint, PassageText, PhotoLocation, Marks, MultiCorrect):
        self.QuestionId = QuestionId
        self.QuestionNumber = QuestionNumber
        self.QuestionText = QuestionText
        self.Options = Options
        self.AnswerKeys = AnswerKeys
        self.Timer = Timer
        self.Hint = Hint
        self.PassageText = PassageText
        self.PhotoLocation = PhotoLocation
        self.Marks = Marks
        self.MultiCorrect = MultiCorrect

    @classmethod
    def get_question_to_object(cls, questionJson):
        QuestionId = questionJson['QuestionId']
        QuestionNumber = questionJson['QuestionNumber']
        QuestionText = questionJson['QuestionText']
        Options = questionJson['Options']
        AnswerKeys = questionJson['AnswerKeys']
        Timer = questionJson['Timer']
        Hint = questionJson['Hint']
        PassageText = questionJson['PassageText']
        PhotoLocation = questionJson['PhotoLocation']
        Marks = questionJson['Marks']
        MultiCorrect = questionJson['MultiCorrect']

        return cls(QuestionId, QuestionNumber, QuestionText, Options, AnswerKeys, Timer,
                   Hint, PassageText, PhotoLocation, Marks, MultiCorrect)

questionJson = [
        {
        "QuestionId": "A101",
        "QuestionNumber": "1",
        "QuestionText": "What is your name?",
        "Options": {
            "A": "Apple",
            "B": "Ball",
            "C": "Cat",
            "D": "Dog",
        },
        "AnswerKeys": ["A"],
        "Timer": "5",
        "Hint": "",
        "PassageText": "",
        "PhotoLocation": "",
        "Marks": "10",
        "MultiCorrect": False
    },
    {
        "QuestionId": "A102",
        "QuestionNumber": "2",
        "QuestionText": "What is your age?",
        "Options": {
            "A": "10",
            "B": "12",
            "C": "14",
            "D": "16",
        },
        "AnswerKeys": ["D"],
        "Timer": "5",
        "Hint": "",
        "PassageText": "",
        "PhotoLocation": "",
        "Marks": "10",
        "MultiCorrect": False
    },
    {
        "QuestionId": "A103",
        "QuestionNumber": "3",
        "QuestionText": "What is your job?",
        "Options": {
            "A": "Sofware Engineer",
            "B": "Defence Officer",
            "C": "Lawyer",
            "D": "Doctor",
        },
        "AnswerKeys": ["A"],
        "Timer": "8",
        "Hint": "",
        "PassageText": "",
        "PhotoLocation": "",
        "Marks": "10",
        "MultiCorrect": False
    }
]

# print(type(questionJson))
# for k, v in questionJson.items():
#     # print(k, v)
#     exec("%s=%s" % (k, v))
#     exec("print(exec('hello'))")
#     # exec('members.append('+str(k)+')')
#     members.append(k)
# print(members)
# return cls(exec("','.join(map(str,members))"))
# questionJson = {"hello": 1, "there": 2}


objects = []
for question in questionJson:
    obj = Question.get_question_to_object(question)
    objects.append(obj)

print(objects[0].QuestionText)
print(objects[1].QuestionText)
print(objects[2].QuestionText)
