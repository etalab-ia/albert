# CI/CD

```mermaid
---
title: "Albert deployment flow"
---
flowchart
	899245["VLLM"] -.-> 905795["VLLM\n[pyalbert/albert.py]\ndownload_models"]
	905795 -.-> 1["VLLM"]
	180724["API"] -.-> 517217["Postprocessing\n[pyalbert/albert.py] \ncreate_whitelist"]
	202492["[pyalbert/config]\nwhitelist_config.json"] --- 517217
	517217 -.-> 233416["API"]
	877037["[pyalbert/config]\nvllm_routing_table.json"] --- 905795
	275863["Deploy"] -.->|"only staging"| 354824[".post"]
	669310[".post"] -.->|"only staging"| 615592["build"]
	556101["[pyalbert/outscale]\nlink_gpu.py"] --- 497453["link gpu"]
	186297["[pyalbert/outscale]\nunlink_gpu.py"] --- 605529["unlink gpu"]
	subgraph 275863["Deploy"]
		1
		233416
	end
	subgraph 615592["build"]
		899245
		180724
	end
	subgraph 536890["Setup"]
		905795
		517217
	end
	subgraph 354824[".post"]
		605529
	end
	subgraph 669310[".post"]
		497453
	end
```

To modify Mermaid flowchart, [click here](https://www.mermaidflow.app/flowchart#N4IgZgNg9g7iBcoB2UAmBTAzgg2qGAlqgC4AWCAzAJwAcANCKegQOanEIBMADBQ0QhCcA7AFYaANgogGAByiYCxAlCQJQADwSjhwgHQUJOmgEYKwsxIn0QAT0pS9VC9wAsRqj0MBfBqgCGxP7qIBD+AEboEIIAIuiy0PYMKBjY8DggJjJCFBSuJhIgALoMmMS2EFi4JSCy-gBO6EjEAEr+SADWCNwM9e1d8Ca9-ZgxfTBqiL4gqOMAyuWVCMT1AK7o0+Wy6IKYq+EsfbLkpVHoAMbE6KgIYP4QmOhyCkoqSACC4ZhQEKtXIVp4Dp9IZjGYLIZrAx7PBDBQnC53KJPLwJNNZv4WCwCEgWLd7o9SosdogQIQSORYbQGExWOwuLxpo1FAAvHF4+B3B4bOj4IhkBCubiiGnMNgceA8HogATwEASEyiZGcbLyRTKVQAwWmPTCQwmTiuKiuURQuwIAC0nEVem4EmFujMbho3BoonRgWCpLCkWicvCqwIEBuyTQVXSIBoVE8JuyJhdwkNxSJFXDOBqdUazTanW6w1zg3zHVG40mwHR82JyzWPJAWxJID2ByOJ0bZ0u13x3L8fSx7K7hNqLw1Hy+Pz+JM02pMuv1huNppsMKtNrtDohztd7pTS1J5IF8CFIsYYvpku43CZWAIbNxA55fIpCAkRtFdIlnHM-BuctEhij3CqsObxakCOh6PaBrcPGJjcMIpiuNCCA6twzgmEawjGs4ngekEIQ+lEghzOgxCrLI2QpGmIBUA6VCiNkogmImTHJo2xJpOmRYlv4EzqEy-QIEMtQNE0rQCfA0oYjACyptW6ybLY2y7Pshz+Mc2SPJUHY-lyg5qq8qifN8vz-KSgJKvokE8DBcEIUh8AoWhGFYZhnAVpi2J3pyBJPGxsl7vylIvlQb7ilw5hXqy-bedyviPge1rSrSYXwDR36CDQui8MIQHqiBZlcAaehCsI0F0a4eqeJwnD2VQM55Ca1qMdQvCcFQuFeqABF+iAOCyLY9yRPUxBFAAOkgABuEAQAAtgA+vUUB-Oyc1BOElR6AAVt8ag7mmNR9J03G8VMcgidm4mSZW-krPJDD1oIjSXO0LCVAAcmGGntlcOk+c8eWGWOJmTiAgLWpwxVwWVogVdQ1U1eaqX1a4jWKmYNEUG17l9l5ukPmSgWCVGoVnmlMo-kI3Dziq-0GWWoOCQUEjFTDuRRrBiV8IjFoSBD8ZUC+nCiBejGuCIHX4REhFyn1A0QENI3jTApBKFEBBlHN5yqGArBbTtGnsdUXFjDxZbTJmok5gMV08TJu63bWD1yk9QS4u9n2nFpP33rTI5GeOplToMTMs64bN1VTsFc8uvN6PzgvC8K6Hiz2HnRXjcUE0+sJUyTH65+TggUDDNBJr7+VB+IzMugLmV6pCjH2RIiZOG1L5hyaUY0BQEvelLPV6GqHChqkuDysKohtaxZSphxB0jCbJ3lkWglnVmYkFjb0lVvADsKUpcpNqp6mexc3sxXpwGA8ZE6gVXeg19Yui5FYjeI83EOeALKN5OItA96nHGHIM68izgeCgBdkpnh4AjWU8oJBUAoLBXKdNQL2lEK3cOFgjRCyEsuYWVA9DNXcJ3U0zhe5dX7oIQeChh4gEohxEAGETTSBqDPSoc9jalj4ivQswl15WzzDMa69saz7wbEfFsX0vadgvr5DEQCfZDgBqOG+gcGbwHQZgigUZsGeDfvg1CRCzAkPEGQ4Q3hM77kpOhRCJ53zIWlHArI5dNQFUPNwAwIhciKkYs3Xmx4YTIi8a6AWfjJCJiMBQ0IVC5QADUAAyCSACy2RDrFkXmbNeltxJCSknbEke97qKQbC7F67sMAoL9kDW+7iFSWUQSYA0ngIFh3smLeEbUTDGiQaE1qrhpiaTPrIvGgDPLAL+vw0SH1KlyhEFXaQVjCaDBRnnRx6U5m5HyIUVx9Mwa8CIZwGg7gUQiDEHkJu8Ji7IhNDg5uwhebRO6oId4AAFAAkgbWeRspkXQLEJdJx0snCNtjvIpdYSmPTPuU9AMydjZOaHCwQ8zJDSFPtpJRCjxlKP0tUtRINATwU8VGMWwsdD5DFngwUIgvEIJRMciEaIlnZ1sWshyTiKZRhjPRXZoE9QP3yK6bZDzSoSHaRgzK6FMKY0TG6eMaI-Ceklr6QQiSUlfI4T8i2fyBgAoXtw06ILt43TEcUg+IAylu1hR7NsMjfrdmUXTf2wM75KiIboHgdUzDFztPZC0BRCH81QkSpBdErDY2xXIhFxAkVygVEqTwIBmUHlZfYlKLoNmZATGXR1I5QKGnhMaMQBQ9RVyVAjGE7gWZ-kntZTC8F2qKrwn3FVco3mfL2pw35G9dVcNNjwo1BS5KO0hc7aFVqkXRtjfKXxib0Xn1GSCxRUbc1vGdbUoOiYMHWEMNs0wMMlR+oKDQCCwpqo4MkKXAWljQHWMEmINlTS7FwJojoOiVSK4aLonoM5FhMJ1QFqVQJlAIZHNLk01CEC-wdyebEkAarknjVloNdAw0xpIFQLAJA0B-CoDmjNMMDwNX7WjYIvhgLMkDvyWC01ELzWWtetayp86RmTNxWump6jARGAhpldmtAqbCFcMc+yTSrlukMK6GgLpMYvgjenNj50Y2fV-P+GiSbb3LKYiFNNZ4zA2DgYxZiOVeXuKQRgpBfGIF1QqtaOxMIdGnsQeIC81V4IWFg62kArzaGyEWucLAihcRIf6ihtD41MMTBw3hgjGAHgAAJxrnEaIEdAc1laqwgOrOh7CSMWv1f2w12qe2r0HTRu6dHSnjsY5O7t06-zWHUyx+1l8VHrq48hFuAHaBGipkLYuonum6jtMLXQzghaYRMPJ3GPlk02NWbpiUGbC5xonlPUzQdPwsw9YxcQphnNLmQq4H9Qm3DfxIRYptnUYledWNhnEHR4ssFkKsYjXaKMGuXt2sjeSRGFNo07C11WKnwrqypkAxdhM5qGRildWKFMOvY9fAOBLnywR-c3fIRyYzHOA-AMQ+gvAIOoK+lhN74rzbsVApbHLBDML-B+txm7PHmCQWICqL431isRkKB+bMmKSFfW+zz0tQgPaey9t7PyPuFa+8Vn7qdjWiIq4DhjIPVRKenVYRpgFms4qvqolHaCHk-rCUYbp+no6WncCe5u39m5MyxwApdkaM41GuCwNMoBAfnFWGUKAM1sgzQaB0VDCwGgShAFAbYu0QDB-qKH+oABRDDgh5A4joRn1D-hLhvAAOrLJ4HtEIZRFqh4Lyyvw6sEj+BhDKe7SAdiDKWvUALGVoyGh5Y2FvAWAAS7RUC7iENkII9RPeR9fZhLvo-x-94w0PlxK2QAe-QBacDporAE7cNkdoBBg-nwdldkvO8Mil6gKH+AABicIJgb-hEKDUbqFeEp2O6r308H5n2YCT6gV4M3Yp65yKZw+5+7EAB5B4h5h6j6R7R5NAQEJ6oYp4Uzp7NDZBZ59C56qDP6UhF5+S7igBn7l5aZV6YA15144hZaN4abd6rCt4NiT7vqlA97oBz6D4Ng0x1gNDj6CCL4z4kSsEL5oEUwr5r5Cza7CZGhCg75IB76pY-iH4zBKqki5ZjyEHoBX53634P78Df6-7KD-6DhP6F6v79zv4OKSgDKAEgLe6jogC+7+6B4MDx6J7h7DSCCwGx7OGIGp5ygoGZ7NDZ6YFIDYEMjF7KErDn7oAhF8K-6kFhDkEN5N5MG0Ft5yjxhwTQ7MECHsEj5cEkSCBGbWgmacFj78ED6CGZoiFMTmAXhWSTzSGyEH41hH7hH+Sn4REX7X635aGsRGHZyGgMBv4f5cBf4-5-4TIAG2rDItb4wgEOHwEuHQHuEx4LHeEUweFoEBEYEjjRG4EqHhFl5RFabN4pENiuAaRZHlE5H3R5GR4wI4K5GlHEDZHIpCGCAiHWCNQXgc6cA7IgC7776sYOoBDNoEEn5sSHEaHdH36sTqxjH6ETGPCDLfRAlImgJzFgGOFx6QH1CuEwErFOE4lIHLFwH8BbE547GF7Sj7FgmHHRFTbJF0HIpUwPGMl95XGvE3FPEFFMRFGPGz4clpFvFyhVGGiJhiAILKgNGAkzEtFgltEQmRFQl37aEyi6HjH3jIl2qanom2H2GYmrG4lLFygbGEkIHJ4+FDgZ6bFXDbH55UlhG0mRH0kkFkGCAUE4hJE0FMm-i8ksRsksGCnD5cncGbJ5AFD8llHz4NiL5wIiEmjCwILBptS67-EyEynDpyl4EkjtGQldEqm9H9y7EmG+hmEpQDFqnwkI5olTGw7WGVaCD6ngFmmLER4kmeFEmWmmn162kUn2n9HUk7xOlEEsonE+mRhZTmAXGnEvFzKRkT60TT63GznBlL4fFHg0TgxIJ-EAlyGYpKHym7i5lKn5k9E1Bwl6HVm1gw4Lqza6nmpNlYleFGltkmkEnYnmnEm+FQDWlkm9lBG7GDn+TDlHGV4zDV7xHumJHUHfCnHIpiCorTl0ErkcF8GR6Q6lznEhlRlsE8HCnL6oCe7+puA+KfFJnSl7m7zNGKGgnZmqEdHqGnkwmP5FlaYGiDGmHDEWE6FVkGG+TPImnYa2DxZlCYj9hanTE6k2EPmgHNkfmtluFvmknyVrFp4-moF-mBGUkDmOmKkjkpqumQVygelUFjmpHwI65IXsnRmcklGhkzoJqoXLlBmxnCGEWr7CzSYoyoRNK6AUVNHrBZn7HHmdGaHMUcW+j0nsU3ZRBlnQKjGXl8URWi6qAQDCWiXYoSV1mzY1ATQEDoAwDyCKVBz+q5AGAb7eW8BNLOB46KieJGBCafjHJGh1THgshQDgESQQSeDdxNL+LFytVMpV6Yh9AzTJIkT+AxAHngUuz5QgAAAqAAQtkGAItM0MkoELaSEMoMQEPjEAQCNf4DNPFvNUoEsOiAQLNRNHllrDNDNKJF2ucGEJgI8HPNMHCRoEVcQK8u0FEAAPIrFUWBUgCvRQDhD3A-6e7zWjqgCoCrD3BKKUHoDQ3mrGQCAMAr4bXmko0NjdlazQD1CCBMWFDTCg3g0QBwo43bW2Fq5Mag741QCE1yiX4Xis2png3nAdCHBLQYYADCPwjNRNYAwtIt2Q4QjNGA9Q-NBNRNbNF4YtEtqG81KsnNjeL1uwPw6NapU1mATAMxliQAA).