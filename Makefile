.RECIPEPREFIX := >
.PHONY: install-minimal install-audio install-vision install-full

install-minimal:
>pip install -e .

install-audio:
>pip install -e .[audio]

install-vision:
>pip install -e .[vision]

install-full:
>pip install -e .[audio,vision,llm,ml,web,network]

