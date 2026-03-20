const form = document.getElementById("leadForm");

form.addEventListener("submit", async function (e) {
  e.preventDefault();

  const name = form.querySelector('input[name="name"]').value.trim();
  const phone = form.querySelector('input[name="phone"]').value.trim();

  try {
    const response = await fetch("https://lead-engine-c8zg.onrender.com/lead", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        name: name,
        phone: phone
      })
    });

    if (!response.ok) {
      throw new Error("Erro ao enviar lead");
    }

    alert("Dados enviados com sucesso!");
    form.reset();
  } catch (error) {
    console.error(error);
    alert("Erro ao enviar os dados.");
  }
});