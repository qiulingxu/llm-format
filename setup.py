from setuptools import setup, find_packages

VERSION = '0.0.0' 
DESCRIPTION = 'llmformat'
LONG_DESCRIPTION = 'Format LLM language by using LALR(1) grammar. Supports JSON, XML, etc.'

# Setting up
setup(
        name="llmformat", 
        version=VERSION,
        author="Qiuling Xu",
        author_email="xennaughtyboy@gmail.com",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=[], # add any additional packages that 
        # needs to be installed along with your package. Eg: 'caer'
        keywords=['python', 'llm', 'format', 'json', 'regex'],
        classifiers= [
        ]
)